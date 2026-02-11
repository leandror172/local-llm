package main

import "fmt"

func add(a int, b int) int {
	return a + b
}

func main() {
	// Bug: passing string where int is expected
	result := add("hello", 42)
	fmt.Println(result)
}
