package main

import (
	"fmt"
	"sync"
	"time"
)

// LRUCache is a generic LRU cache with TTL expiration
type LRUCache[K comparable, V any] struct {
	mu          sync.RWMutex
	capacity    int
	entries     map[K]*entry[K, V]
	head        *listNode[K, V]
	tail        *listNode[K, V]
	cleanupInterval time.Duration
}

// entry represents a cache entry with value and expiration time
type entry[K comparable, V any] struct {
	value      V
	expiresAt  time.Time
	node       *listNode[K, V]
}

// listNode represents a node in the doubly linked list
type listNode[K comparable, V any] struct {
	key   K
	value V
	prev  *listNode[K, V]
	next  *listNode[K, V]
}

// NewLRUCache creates a new LRU cache with specified capacity and cleanup interval
func NewLRUCache[K comparable, V any](capacity int, cleanupInterval time.Duration) *LRUCache[K, V] {
	if capacity <= 0 {
		panic("capacity must be positive")
	}
	return &LRUCache[K, V]{
		capacity:    capacity,
		entries:     make(map[K]*entry[K, V]),
		cleanupInterval: cleanupInterval,
	}
}

// Get retrieves a value from the cache, automatically evicting expired entries
func (c *LRUCache[K, V]) Get(key K) (V, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()

	entry, ok := c.entries[key]
	if !ok {
		return V{}, false
	}

	if time.Now().After(entry.expiresAt) {
		delete(c.entries, key)
		c.removeNode(entry.node)
		return V{}, false
	}

	// Move to front (mark as recently used)
	c.moveToFront(entry.node)
	return entry.value, true
}

// Put adds or updates a key-value pair with a specified TTL
func (c *LRUCache[K, V]) Put(key K, value V, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	entry, ok := c.entries[key]
	if ok {
		entry.value = value
		entry.expiresAt = time.Now().Add(ttl)
		c.moveToFront(entry.node)
		return
	}

	// Evict LRU entry if cache is full
	if len(c.entries) >= c.capacity {
		if c.tail != nil {
			c.removeNode(c.tail)
			delete(c.entries, c.tail.key)
		}
	}

	newNode := &listNode[K, V]{key: key, value: value}
	newEntry := &entry[K, V]{value: value, expiresAt: time.Now().Add(ttl), node: newNode}
	c.entries[key] = newEntry

	c.moveToFront(newNode)
}

// Delete removes a key-value pair from the cache
func (c *LRUCache[K, V]) Delete(key K) {
	c.mu.Lock()
	defer c.mu.Unlock()

	entry, ok := c.entries[key]
	if !ok {
		return
	}

	c.removeNode(entry.node)
	delete(c.entries, key)
}

// startCleanup starts a background goroutine that periodically cleans expired entries
func (c *LRUCache[K, V]) startCleanup() {
	ticker := time.NewTicker(c.cleanupInterval)
	go func() {
		for range ticker.C {
			c.mu.Lock()
			// Check for expired entries
			for key, entry := range c.entries {
				if time.Now().After(entry.expiresAt) {
					delete(c.entries, key)
					c.removeNode(entry.node)
				}
			}
			c.mu.Unlock()
		}
	}()
}

// removeNode removes a node from the doubly linked list
func (c *LRUCache[K, V]) removeNode(node *listNode[K, V]) {
	if node == nil {
		return
	}

	if node == c.head {
		c.head = node.next
	}

	if node == c.tail {
		c.tail = node.prev
	}

	if node.prev != nil {
		node.prev.next = node.next
	}

	if node.next != nil {
		node.next.prev = node.prev
	}
}

// moveToFront moves a node to the front of the linked list
func (c *LRUCache[K, V]) moveToFront(node *listNode[K, V]) {
	if node == c.head {
		return
	}

	c.removeNode(node)

	node.next = c.head
	node.prev = nil

	if c.head != nil {
		c.head.prev = node
	}

	c.head = node

	if c.tail == nil {
		c.tail = node
	}
}

func main() {
	// Create a cache with capacity 3 and cleanup interval of 2 seconds
	cache := NewLRUCache[string, string](3, 2*time.Second)
	cache.startCleanup()

	// Create 3 concurrent goroutines performing Get/Put operations
	for i := 0; i < 3; i++ {
		go func(id int) {
			for {
				key := fmt.Sprintf("key%d", id)
				value := fmt.Sprintf("value%d", id)
				cache.Put(key, value, 5*time.Second)
				time.Sleep(1 * time.Second)
				val, ok := cache.Get(key)
				if ok {
					fmt.Printf("Goroutine %d: Got %s: %s\n", id, key, val)
				} else {
					fmt.Printf("Goroutine %d: Key %s not found\n", id, key)
			
				}
				time.Sleep(1 * time.Second)
			}
		}(i)
	}

	// Keep the main goroutine alive
	select {}
}