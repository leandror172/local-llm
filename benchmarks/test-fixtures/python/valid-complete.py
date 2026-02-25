"""Word frequency counter — complete module with typed functions."""

from collections import Counter
import re
import sys


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words."""
    return re.findall(r"[a-z']+", text.lower())


def top_words(text: str, n: int = 10) -> list[tuple[str, int]]:
    """Return the n most common words in text."""
    tokens = tokenize(text)
    return Counter(tokens).most_common(n)


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "to be or not to be that is the question"
    for word, count in top_words(sample):
        print(f"{count:4d}  {word}")
