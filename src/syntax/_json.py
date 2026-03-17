from __future__ import annotations

import re
from typing import Any, ClassVar

from rich.style import Style

from syntax import SyntaxStyle, Token


class JsonSyntaxStyle(SyntaxStyle):
	NUMBER_RE: ClassVar[re.Pattern[str]] = re.compile(
		r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?"
	)

	@property
	def mode(self) -> str:
		return "json"

	def initial_state(self) -> bool:
		return False

	def tokenize_line(self, line: str, state: Any) -> tuple[list[Token], Any]:
		tokens: list[Token] = []
		line_len = len(line)
		i = 0
		in_string = bool(state)

		while i < line_len:
			char = line[i]

			if in_string:
				end, closed = self.consume_string(line, -1, '"')
				tokens.append((0, end, "string"))
				return tokens, not closed

			if char.isspace():
				i += 1
				continue

			if char == '"':
				end, closed = self.consume_string(line, i, '"')
				token_name = "string"
				if closed and self.next_non_whitespace_char(line, end) == ":":
					token_name = "json.label"
				tokens.append((i, end, token_name))
				i = end
				if not closed:
					return tokens, True
				continue

			number_match = self.NUMBER_RE.match(line, i)
			if number_match is not None:
				tokens.append((i, number_match.end(), "number"))
				i = number_match.end()
				continue

			if line.startswith("true", i) and self.is_boundary(line, i, 4):
				tokens.append((i, i + 4, "boolean"))
				i += 4
				continue

			if line.startswith("false", i) and self.is_boundary(line, i, 5):
				tokens.append((i, i + 5, "boolean"))
				i += 5
				continue

			if line.startswith("null", i) and self.is_boundary(line, i, 4):
				tokens.append((i, i + 4, "json.null"))
				i += 4
				continue

			if char in "{}[],:":
				tokens.append((i, i + 1, "punctuation"))
				i += 1
				continue

			i += 1

		return tokens, False

	def theme_styles(self) -> dict[str, Style]:
		return {
			"json.label": Style.parse("bold #7FDBCA"),
			"json.null": Style.parse("#FFB86C"),
			"string": Style.parse("#F2A65A"),
			"number": Style.parse("#8DD3C7"),
			"boolean": Style.parse("#FF8A65"),
			"punctuation": Style.parse("#B0BEC5"),
		}