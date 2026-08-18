package main

import (
	"container/list"
	"errors"
	"sync"
	"time"
)

type CacheKey interface{}
type CacheValue interface{}

type cacheEntry struct {
	key      CacheKey
	value    CacheValue
	expiration time.Time
}

type LRUCache[K CacheKey, V CacheValue] struct {
	maxSize int
	ttl     time.Duration
	cache   map[K]*list.Element
	ll      *list.List
	mu      sync.RWMutex
	wg      sync.WaitGroup
	stopCh  chan struct{}
}

func NewLRUCache[K CacheKey, V CacheValue](maxSize int, ttl time.Duration) *LRUCache[K, V] {
	c := &LRUCache[K, V]{
		maxSize: maxSize,
		ttl:     ttl,
		cache:   make(map[K]*list.Element),
		ll:      list.New(),
		stopCh:  make(chan struct{}),
	}
	go c.backgroundEviction()
	return c
}

func (c *LRUCache[K, V]) backgroundEviction() {
	ticker := time.NewTicker(c.ttl)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.evictExpiredEntries()
		case <-c.stopCh:
			return
		}
	}
}

func (c *LRUCache[K, V]) evictExpiredEntries() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for e := c.ll.Front(); e != nil; {
		entry := e.Value.(*cacheEntry)
		if entry.expiration.Before(now) {
			delete(c.cache, entry.key)
			c.ll.Remove(e)
			e = c.ll.Front()
		} else {
			break
		}
	}
}

func (c *LRUCache[K, V]) Get(key K) (V, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if e, found := c.cache[key]; found {
		entry := e.Value.(*cacheEntry)
		if entry.expiration.Before(time.Now()) {
			delete(c.cache, key)
			c.ll.Remove(e)
			return *new(V), errors.New("entry expired")
		}
		c.ll.MoveToFront(e)
		return entry.value.(V), nil
	}
	var zero V
	return zero, errors.New("key not found")
}

func (c *LRUCache[K, V]) Put(key K, value V) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if e, found := c.cache[key]; found {
		entry := e.Value.(*cacheEntry)
		entry.value = value
		entry.expiration = time.Now().Add(c.ttl)
		c.ll.MoveToFront(e)
		return
	}

	if len(c.cache) >= c.maxSize {
		lru := c.ll.Back()
		if lru != nil {
			entry := lru.Value.(*cacheEntry)
			delete(c.cache, entry.key)
			c.ll.Remove(lru)
		}
	}

	newEntry := &cacheEntry{
		key:      key,
		value:    value,
		expiration: time.Now().Add(c.ttl),
	}
	e := c.ll.PushFront(newEntry)
	c.cache[key] = e
}

func (c *LRUCache[K, V]) Delete(key K) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if e, found := c.cache[key]; found {
		delete(c.cache, key)
		c.ll.Remove(e)
	}
}

func main() {
	cache := NewLRUCache[string, int](3, 5*time.Second)

	wg := &sync.WaitGroup{}
	wg.Add(3)

	go func() {
		defer wg.Done()
		for i := 0; i < 10; i++ {
			val, err := cache.Get("key" + strconv.Itoa(i))
			if err != nil {
				fmt.Println(err)
			} else {
				fmt.Println("Get key", "key"+strconv.Itoa(i), "value:", val)
			}
			time.Sleep(1 * time.Second)
		}
	}()

	go func() {
		defer wg.Done()
		for i := 0; i < 5; i++ {
			cache.Put("key" + strconv.Itoa(i), i*10)
			fmt.Println("Put key", "key"+strconv.Itoa(i), "value:", i*10)
			time.Sleep(2 * time.Second)
		}
	}()

	go func() {
		defer wg.Done()
		for i := 5; i < 10; i++ {
			cache.Put("key" + strconv.Itoa(i), i*10)
			fmt.Println("Put key", "key"+strconv.Itoa(i), "value:", i*10)
			time.Sleep(2 * time.Second)
		}
	}()

	wg.Wait()
	close(cache.stopCh)
}