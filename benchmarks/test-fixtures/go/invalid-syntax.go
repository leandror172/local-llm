package main

import "fmt"

func greet(name string) string {
	// Bug: missing closing brace for if
	if name == "" {
		return "Hello, stranger!"

	return fmt.Sprintf("Hello, %s!", name)
}
