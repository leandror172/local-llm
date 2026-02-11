package main

import "fmt"

func main() {
	// Bug: 'result' is never declared
	fmt.Println(result)
}
