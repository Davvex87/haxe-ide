from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeAlias

from rich.style import Style

Token: TypeAlias = tuple[int, int, str]


class SyntaxStyle(ABC):
    """Contract for line-based fallback syntax tokenizers."""

    @staticmethod
    def consume_string(line: str, start: int, quote: str) -> tuple[int, bool]:
        i = start + 1
        escaped = False
        while i < len(line):
            char = line[i]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                return i + 1, True
            i += 1
        return i, False

    @staticmethod
    def next_non_whitespace_char(line: str, start: int) -> str | None:
        i = start
        while i < len(line):
            if not line[i].isspace():
                return line[i]
            i += 1
        return None

    @staticmethod
    def previous_non_whitespace_char(line: str, start: int) -> str | None:
        i = start - 1
        while i >= 0:
            if not line[i].isspace():
                return line[i]
            i -= 1
        return None

    @staticmethod
    def is_boundary(line: str, start: int, length: int) -> bool:
        before = line[start - 1] if start > 0 else None
        after_index = start + length
        after = line[after_index] if after_index < len(line) else None
        return (before is None or not before.isalnum()) and (after is None or not after.isalnum())

    @property
    @abstractmethod
    def mode(self) -> str:
        """Unique syntax mode name (e.g. haxe, json)."""

    @abstractmethod
    def initial_state(self) -> Any:
        """Return a fresh tokenizer state for the start of a document."""

    @abstractmethod
    def tokenize_line(self, line: str, state: Any) -> tuple[list[Token], Any]:
        """Tokenize a single line and return (tokens, next_state)."""

    @abstractmethod
    def theme_styles(self) -> dict[str, Style]:
        """Return token-name -> style mappings used by this syntax mode."""