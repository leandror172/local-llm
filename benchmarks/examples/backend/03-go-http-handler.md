---
id: ex-03-go-http-handler
category: backend
type: few-shot-example
demonstrates: complete program with main(), net/http, error handling
---

## Task

HTTP health check endpoint returning JSON.

## Input

Write a Go program with a GET /health endpoint that returns a JSON response with status "ok" and the current server time. Include proper error handling and Content-Type headers.

## Output

```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

type HealthResponse struct {
	Status string `json:"status"`
	Time   string `json:"time"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	resp := HealthResponse{
		Status: "ok",
		Time:   time.Now().UTC().Format(time.RFC3339),
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("encode response: %v", err)
	}
}

func main() {
	http.HandleFunc("/health", healthHandler)
	log.Println("listening on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
```
