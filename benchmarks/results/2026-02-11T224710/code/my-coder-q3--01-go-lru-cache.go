package main

import (
	"fmt"
	"sync"
	"time"
)

type LRUCache[K comparable, V any] struct {
	entries map[K]struct {
		value    V
		expires  time.Time
	}
	order    []K
	capacity int
	mu       sync.RWMutex
	ticker   *time.Ticker
}

func NewLRUCache[K comparable, V any](capacity int) *LRUCache[K, V] {
	if capacity <= 0 {
		panic("capacity must be positive")
	}
	return &LRUCache[K, V]{
		entries: make(map[K]struct {
			value    V
			expires  time.Time
		}),
		capacity: capacity,
	}
}

func (c *LRUCache[K, V]) Get(key K) (V, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, ok := c.entries[key]
	if !ok {
		return *new(V), fmt.Errorf("key not found")
	}

	if time.Now().After(entry.expires) {
		c.mu.Lock()
		defer c.mu.Unlock()
		delete(c.entries, key)
		for i, k := range c.order {
			if k == key {
				c.order = append(c.order[:i], c.order[i+1:]...)
				break
			}
		}
		return *new(V), fmt.Errorf("key expired")
	}

	c.mu.Lock()
	defer c.mu.Unlock()
	for i, k := range c.order {
		if k == key {
			c.order = append(c.order[:i], c.order[i+1:]...)
			break
		}
	}
	c.order = append([]K{key}, c.order...)
	return entry.value, nil
}

func (c *LRUCache[K, V]) Put(key K, value V, ttl time.Duration) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	expires := now.Add(ttl)

	if existing, ok := c.entries[key]; ok {
		existing.value = value
		existing.expires = expires
		for i, k := range c.order {
			if k == key {
				c.order = append(c.order[:i], c.order[i+1:]...)
				break
			}
		}
		c.order = append([]K{key}, c.order...)
		return nil
	}

	c.entries[key] = struct {
		value    V
		expires  time.Time
	}{
		value:    value,
		expires:  expires,
	}
	c.order = append([]K{key}, c.order...)
	if len(c.order) > c.capacity {
		last := c.order[len(c.order)-1]
		delete(c.entries, last)
		c.order = c.order[:len(c.order)-1]
	}
	return nil
}

func (c *LRUCache[K, V]) Delete(key K) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if _, ok := c.entries[key]; !ok {
		return fmt.Errorf("key not found")
	}

	delete(c.entries, key)
	for i, k := range c.order {
		if k == key {
			c.order = append(c.order[:i], c.order[i+1:]...)
			break
		}
	}
	return nil
}

func (c *LRUCache[K, V]) StartCleanup(interval time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.ticker != nil {
		c.ticker.Stop()
	}
	c.ticker = time.NewTicker(interval)
	go func() {
		for range c.ticker.C {
			c.mu.Lock()
			c.cleanup()
			c.mu.Unlock()
		}
	}()
}

func (c *LRUCache[K, V]) cleanup() {
	now := time.Now()
	toDelete := make([]K, 0, len(c.entries))
	for key, entry := range c.entries {
		if now.After(entry.expires) {
			toDelete = append(toDelete, key)
		}
	}
	for _, key := range toDelete {
		delete(c.entries, key)
		for i, k := range c.order {
			if k == key {
				c.order = append(c.order[:i], c.order[i+1:]...)
				break
			}
		}
	}
}

func main() {
	cache := NewLRUCache[string, string](3)
	cache.StartCleanup(1 * time.Second)

	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 10; j++ {
				key := fmt.Sprintf("key%d", id)
				value := fmt.Sprintf("value%d", id)
				if err := cache.Put(key, value, 5*time.Second); err != nil {
					fmt.Printf("Goroutine %d: Put error: %v\n", id, err)
				}
				time.Sleep(time.Millisecond * 500)
				val, err := cache.Get(key)
				if err != nil {
					fmt.Printf("Goroutine %d: Get error: %v\n", id, err)
				} else {
					fmt.Printf("Goroutine %d: Got %s\n", id, val)
				}
			}
		}(i)
	}
	wg.Wait()
}