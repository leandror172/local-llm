# retrieval/routing.py

from typing import Set
from pathlib import Path


CODE_EXTENSIONS: Set[str] = {".py", ".go", ".ts", ".java"}


def route(path: str) -> str:
    ext = _get_extension(path)
    return "extraction_code" if ext in CODE_EXTENSIONS else "extraction_prose"


def _get_extension(path: str) -> str:
    path_obj = Path(path)
    return path_obj.suffix.lower()
