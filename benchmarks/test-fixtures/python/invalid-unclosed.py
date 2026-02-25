# Bug: unclosed parenthesis in return statement (SyntaxError).


def format_record(name: str, score: int) -> str:
    return (
        f"Name: {name}, Score: {score}"
