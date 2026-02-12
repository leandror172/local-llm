---
id: ex-01-go-error-handling
category: backend
type: few-shot-example
demonstrates: error wrapping with %w, stdlib only, no over-engineering
---

## Task

Read a JSON configuration file and return a typed struct.

## Input

Write a Go function that reads a JSON file at a given path and returns a Config struct with fields: Host (string), Port (int), Debug (bool). Handle all errors with context wrapping.

## Output

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Config struct {
	Host  string `json:"host"`
	Port  int    `json:"port"`
	Debug bool   `json:"debug"`
}

func LoadConfig(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read config %s: %w", path, err)
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config %s: %w", path, err)
	}

	return cfg, nil
}

func main() {
	cfg, err := LoadConfig("config.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("host=%s port=%d debug=%v\n", cfg.Host, cfg.Port, cfg.Debug)
}
```
