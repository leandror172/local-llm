package main

import (
	"container/list"
	"fmt"
	"sync"
	"time"
)

// LRUCache is a concurrent-safe LRU cache with TTL.
type LRUCache[K comparable, V any] struct {
	capacity int
	ttl      time.Duration
	items    map[K]*list.Element
	list     *list.List
	mu       sync.RWMutex
	done     chan bool
}

// entry represents a key-value pair in the cache.
type entry[K comparable, V any] struct {
	key   K
	value V
	expiry time.Time
}

// NewLRUCache creates a new LRUCache with the given capacity and TTL.
func NewLRUCache[K comparable, V any](capacity int, ttl time.Duration) *LRUCache[K, V] {
	cache := &LRUCache[K, V]{
		capacity: capacity,
		ttl:      ttl,
		items:    make(map[K]*list.Element),
		list:     list.New(),
		done:     make(chan bool),
	}
	go cache.startCleanup()
	return cache
}

// Get retrieves the value associated with a key if it exists and is not expired.
func (c *LRUCache[K, V]) Get(key K) (V, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if elem, ok := c.items[key]; ok {
		entry := elem.Value.(*entry[K, V])
		if time.Now().After(entry.expiry) {
			c.evict(elem)
			return *new(V), false
		}
		c.list.MoveToFront(elem)
		return entry.value, true
	}
	return *new(V), false
}

// Put adds a key-value pair to the cache with a specified TTL.
func (c *LRUCache[K, V]) Put(key K, value V) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if elem, ok := c.items[key]; ok {
		entry := elem.Value.(*entry[K, V])
		entry.value = value
		entry.expiry = time.Now().Add(c.ttl)
		c.list.MoveToFront(elem)
		return
	}

	elem := c.list.PushFront(&entry[K, V]{key: key, value: value, expiry: time.Now().Add(c.ttl)})
	c.items[key] = elem

	if c.list.Len() > c.capacity {
		c.evict(c.list.Back())
	}
}

// Delete removes a key-value pair from the cache.
func (c *LRUCache[K, V]) Delete(key K) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if elem, ok := c.items[key]; ok {
		c.evict(elem)
	}
}

// evict removes an element from the cache and updates the map.
func (c *LRUCache[K, V]) evict(elem *list.Element) {
	entry := elem.Value.(*entry[K, V])
	delete(c.items, entry.key)
	c.list.Remove(elem)
}

// startCleanup runs in a background goroutine to periodically clean up expired entries.
func (c *LRUCache[K, V]) startCleanup() {
	ticker := time.NewTicker(1 * time.Second) // Adjust the interval as needed
	defer ticker.Stop()
	defer close(c.done)

	for {
		select {
		case <-ticker.C:
			c.mu.Lock()
			now := time.Now()
			for elem := c.list.Back(); elem != nil; {
				entry := elem.Value.(*entry[K, V])
				if now.After(entry.expiry) {
					next := elem.Prev()
					c.evict(elem)
					elem = next
				} else {
					break
				}
			}
			c.mu.Unlock()
		case <-c.done:
			return
		}
	}
}

// main demonstrates the usage of the LRUCache with concurrent goroutines.
func main() {
	cache := NewLRUCache[string, int](3, 5*time.Second)

	go func() {
		for i := 0; i < 10; i++ {
			cache.Put(fmt.Sprintf("key%d", i), i)
			fmt.Printf("Put key%d: %d\n", i, i)
			time.Sleep(2 * time.Second)
		}
	}()

	go func() {
		for i := 0; i < 5; i++ {
			if value, ok := cache.Get(fmt.Sprintf("key%d", i)); ok {
				fmt.Printf("Get key%d: %d\n", i, value)
			} else {
				fmt.Printf("Get key%d: Not found\n", i)
			}
			time.Sleep(1 * time.Second)
		}
	}()

	go func() {
		for i := 5; i < 10; i++ {
			if value, ok := cache.Get(fmt.Sprintf("key%d", i)); ok {
				fmt.Printf("Get key%d: %d\n", i, value)
			} else {
				fmt.Printf("Get key%d: Not found\n", i)
			}
			time.Sleep(1 * time.Second)
		}
	}()

	select {}
}