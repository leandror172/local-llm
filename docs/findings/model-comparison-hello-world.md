# Model Comparison: Qwen2.5-Coder-7B vs Claude Opus 4.6

**Date:** 2026-02-06
**Prompt:** "Write a hello world function in Go"
**System prompt (both models):** Java/Go backend expert, SOLID principles, idiomatic code, production-ready

---

## Qwen2.5-Coder-7B (`my-coder`, Docker, RTX 3060 12GB)

**Performance:** 64.26 tok/s | 228 tokens | 3.55s eval

```go
package main

import (
	"fmt"
)

// HelloWorld prints "Hello, World!" to the console.
func HelloWorld() {
	fmt.Println("Hello, World!")
}

func main() {
	// Call the HelloWorld function
	HelloWorld()
}
```

### Explanation (model output)

1. **Package Declaration**: `package main` declares that this is a standalone executable program.
2. **Import Statement**: `import "fmt"` imports the `fmt` package, which provides functions for formatted I/O operations like printing to the console.
3. **Function Definition**: `HelloWorld()` is a function that prints "Hello, World!" to the console using `fmt.Println()`.
4. **Main Function**: The `main()` function is the entry point of a Go program. It calls the `HelloWorld()` function to execute the code.

This code follows the SOLID principles by being simple and focused on a single responsibility (printing "Hello, World!"). It also adheres to idiomatic Go practices by using standard library functions for output.

---

## Claude Opus 4.6 (API, frontier model)

```go
package main

import "fmt"

func helloWorld() string {
	return "Hello, World!"
}

func main() {
	fmt.Println(helloWorld())
}
```

### Explanation (model output)

- `helloWorld()` is a simple function that returns the string `"Hello, World!"`. It takes no parameters and returns a `string`.
- `main()` is the entry point of every Go executable. It calls `helloWorld()` and prints the result to stdout using `fmt.Println`.

**Why return a string instead of printing directly inside the function?** Separating the message construction from the I/O makes the function easier to test. You can write a straightforward unit test like this:

```go
package main

import "testing"

func TestHelloWorld(t *testing.T) {
	expected := "Hello, World!"
	got := helloWorld()

	if got != expected {
		t.Errorf("helloWorld() = %q, want %q", got, expected)
	}
}
```

This follows the idiomatic Go practice of keeping functions pure where possible and pushing side effects (like printing) to the caller.

---

## Analysis

### Code Quality

| Aspect | Qwen 7B | Claude Opus |
|--------|---------|-------------|
| **Function signature** | `func HelloWorld()` — prints directly | `func helloWorld() string` — returns a string |
| **Separation of concerns** | I/O inside the function | I/O pushed to caller |
| **Testability** | Not easily testable (side effect) | Testable — included unit test |
| **Naming convention** | `HelloWorld` (exported) | `helloWorld` (unexported) |
| **Import style** | Grouped block | Single inline |
| **Comments** | Godoc-style on function | None needed (self-documenting) |

### Explanation Quality

| Aspect | Qwen 7B | Claude Opus |
|--------|---------|-------------|
| **Structure** | Numbered list of 4 points | Prose + code blocks |
| **SOLID compliance** | Superficial — lists all 5 principles, admits 3 don't apply | Demonstrates SRP implicitly through design |
| **Practical extras** | None | `go run` command + unit test |
| **Reasoning depth** | Explains *what* each part is | Explains *why* the design choice matters |

### Key Observations

1. **Pure function vs side effect**: Claude's design separates computation from I/O, making it testable. Qwen's version embeds the side effect, which is functional but less idiomatic for production Go.

2. **The SOLID trap**: Qwen tried to explicitly map all 5 SOLID principles to a hello world — an overreach for the task. Claude demonstrated the principle (testability = SRP) without forcing the label.

3. **Naming**: Qwen exported the function (`HelloWorld`), Claude kept it unexported (`helloWorld`). For an internal helper in `package main`, unexported is more idiomatic — nothing outside the package needs to call it.

4. **The gap is in reasoning, not syntax**: Both models produced correct, compilable Go. The difference is in architectural thinking — when to return vs print, why testability matters, what deserves exporting.

---

## Reproducing This Comparison

```bash
# Local model (Docker)
curl -s http://localhost:11434/api/chat -d '{
  "model": "my-coder",
  "messages": [{"role": "user", "content": "Write a hello world function in Go"}],
  "stream": false
}' | python3 -m json.tool

# To compare with other local models, swap "my-coder" for any model name
```

For Claude API comparison, use the Anthropic API with the same system prompt from `modelfiles/coding-assistant.Modelfile`.
