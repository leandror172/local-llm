# Bug: missing colon after function signature (SyntaxError).


def greet(name: str) -> str
    if not name:
        return "Hello, stranger!"
    return f"Hello, {name}!"
