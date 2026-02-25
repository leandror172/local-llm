# Bug: over-indented return statement (IndentationError).


def compute(x: int, y: int) -> int:
    result = x + y
      return result
