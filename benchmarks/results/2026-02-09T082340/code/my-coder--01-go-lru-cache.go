package main

import (
	"container/list"
	"errors"
	"fmt"
	"sync"
	"time"
)

// LRUCache represents an LRU cache with TTL expiration.
type LRUCache[K comparable, V any] struct {
	capacity int
	ttl      time.Duration
	cache    map[K]*list.Element
	ll       *list.List
	mu       sync.RWMutex
	stopChan chan struct{}
	wg       sync.WaitGroup
}

// entry is a cache entry with key, value, and expiration time.
type entry[K comparable, V any] struct {
	key        K
	value      V
	expiration time.Time
}

// NewLRUCache creates a new LRUCache instance.
func NewLRUCache[K comparable, V any](capacity int, ttl time.Duration) *LRUCache[K, V] {
	lru := &LRUCache[K, V]{
		capacity: capacity,
		ttl:      ttl,
		cache:    make(map[K]*list.Element),
		ll:       list.New(),
		stopChan: make(chan struct{}),
	}
	go lru.startCleanup()
	return lru
}

// startCleanup starts a background goroutine to periodically clean up expired entries.
func (lru *LRUCache[K, V]) startCleanup() {
	lru.wg.Add(1)
	defer lru.wg.Done()

	ticker := time.NewTicker(lru.ttl / 2) // Half of the TTL for cleanup
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			lru.mu.Lock()
			for e := lru.ll.Front(); e != nil; {
				elem := e.Value.(*entry[K, V])
				if time.Now().After(elem.expiration) {
					delete(lru.cache, elem.key)
					lru.ll.Remove(e)
				}
				e = e.Next()
			}
			lru.mu.Unlock()
		case <-lru.stopChan:
			return
		}
	}
}

// Stop stops the background cleanup goroutine.
func (lru *LRUCache[K, V]) Stop() {
	close(lru.stopChan)
	lru.wg.Wait()
}

// Get retrieves a value from the cache by key. It evicts expired entries on access.
func (lru *LRUCache[K, V]) Get(key K) (V, error) {
	lru.mu.Lock()
	defer lru.mu.Unlock()

	elem, ok := lru.cache[key]
	if !ok || time.Now().After(elem.Value.(*entry[K, V]).expiration) {
		return zeroValue[V](), errors.New("key not found or expired")
	}

	// Move the accessed entry to the front of the list
	lru.ll.MoveToFront(elem)
	return elem.Value.(*entry[K, V]).value, nil
}

// Put adds a key-value pair to the cache with TTL expiration.
func (lru *LRUCache[K, V]) Put(key K, value V) {
	lru.mu.Lock()
	defer lru.mu.Unlock()

	if elem, ok := lru.cache[key]; ok {
		elem.Value.(*entry[K, V]).value = value
		elem.Value.(*entry[K, V]).expiration = time.Now().Add(lru.ttl)
		lru.ll.MoveToFront(elem)
		return
	}

	newElem := &list.Element{Value: &entry[K, V]{key, value, time.Now().Add(lru.ttl)}}
	lru.cache[key] = newElem
	lru.ll.PushFront(newElem)

	if lru.ll.Len() > lru.capacity {
		elem := lru.ll.Back()
		delete(lru.cache, elem.Value.(*entry[K, V]).key)
		lru.ll.Remove(elem)
	}
}

// Delete removes a key-value pair from the cache.
func (lru *LRUCache[K, V]) Delete(key K) {
	lru.mu.Lock()
	defer lru.mu.Unlock()

	if elem, ok := lru.cache[key]; ok {
		delete(lru.cache, key)
		lru.ll.Remove(elem)
	}
}

// zeroValue returns the zero value of type V.
func zeroValue[V any]() V {
	var v V
	return v
}

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
		for i := 0; i < 10; i++ {
			val, err := cache.Get(fmt.Sprintf("key%d", i))
			if err != nil {
				fmt.Printf("Get key%d: %v\n", i, err)
			} else {
				fmt.Printf("Get key%d: %d\n", i, val)
			}
			time.Sleep(1 * time.Second)
		}
	}()

	go func() {
		for i := 0; i < 10; i++ {
			cache.Delete(fmt.Sprintf("key%d", i))
			fmt.Printf("Delete key%d\n", i)
			time.Sleep(3 * time.Second)
		}
	}()

	time.Sleep(20 * time.Second)
	cache.Stop()
}