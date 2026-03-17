from __future__ import annotations

import re
from typing import Any, ClassVar

from rich.style import Style

from syntax import SyntaxStyle, Token


class CodeSyntaxStyle(SyntaxStyle):
	"""Shared tokenizer for C-style languages with similar lexical structure."""

	MODE: ClassVar[str] = "code"

	KEYWORDS_DECLARATION: ClassVar[set[str]] = set()
	KEYWORDS_CONTROL: ClassVar[set[str]] = set()
	KEYWORDS_FLOW: ClassVar[set[str]] = set()
	KEYWORDS_MISC: ClassVar[set[str]] = set()

	BOOLEAN_LITERALS: ClassVar[set[str]] = {"true", "false"}
	NULL_LITERAL: ClassVar[str] = "null"
	TYPE_EXPECTING_KEYWORDS: ClassVar[set[str]] = set()
	VARIABLE_DECLARATION_KEYWORDS: ClassVar[set[str]] = {"var", "final"}
	FUNCTION_DECLARATION_KEYWORD: ClassVar[str] = "function"

	IDENTIFIER_RE: ClassVar[re.Pattern[str]] = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
	NUMBER_RE: ClassVar[re.Pattern[str]] = re.compile(
		r"(?:0[xX][0-9A-Fa-f_]+|(?:\d+(?:_\d+)*(?:\.\d+(?:_\d+)*)?|\.\d+)(?:[eE][+-]?\d+)?)"
	)

	ENABLE_COMPILER_DIRECTIVE: ClassVar[bool] = True
	COMPILER_RE: ClassVar[re.Pattern[str] | None] = re.compile(r"#[_A-Za-z][_A-Za-z0-9]*")

	ENABLE_METADATA: ClassVar[bool] = True
	METADATA_RE: ClassVar[re.Pattern[str] | None] = re.compile(r"@:?[_A-Za-z][_A-Za-z0-9]*")

	LINE_COMMENT_PREFIX: ClassVar[str | None] = "//"
	BLOCK_COMMENT_START: ClassVar[str | None] = "/*"
	BLOCK_COMMENT_END: ClassVar[str | None] = "*/"

	STRING_QUOTES: ClassVar[tuple[str, ...]] = ('"', "'")

	OPERATORS: ClassVar[tuple[str, ...]] = (
		">>>=",
		"<<=",
		">>=",
		"===",
		"!==",
		"==",
		"!=",
		">=",
		"<=",
		"&&",
		"||",
		"->",
		"=>",
		"+=",
		"-=",
		"*=",
		"/=",
		"%=",
		"&=",
		"|=",
		"^=",
		"<<",
		">>",
		">>>",
		"??",
		"?.",
		"::",
		"...",
		"++",
		"--",
	)
	SINGLE_OPERATORS: ClassVar[set[str]] = set("=+-*/%<>!&|^~?:")
	PUNCTUATION: ClassVar[set[str]] = set("(){}[];,.:")

	# TODO: I just had ChatGPT do the styling here, I'm really not good at picking colors
	# Make your own styles and submit a PR if you think you can do better!
	THEME_STYLES: ClassVar[dict[str, Style]] = {
		"comment": Style.parse("italic #5C6370"),
		"string": Style.parse("#98C379"),
		"number": Style.parse("#D19A66"),
		"boolean": Style.parse("bold #E06C75"),
		"keyword": Style.parse("bold #61AFEF"),
		"keyword.control": Style.parse("bold #C678DD"),
		"keyword.return": Style.parse("bold #FF5370"),
		"keyword.operator": Style.parse("#56B6C2"),
		"class": Style.parse("bold #E5C07B"),
		"type": Style.parse("#56B6C2"),
		"function": Style.parse("#61AFEF"),
		"function.call": Style.parse("#82AAFF"),
		"variable": Style.parse("#ABB2BF"),
		"constant.builtin": Style.parse("bold #D19A66"),
		"punctuation": Style.parse("#3E4451")
	}

	@property
	def mode(self) -> str:
		return self.MODE

	def initial_state(self) -> dict[str, Any]:
		return {"in_block_comment": False, "in_string": None}

	def tokenize_line(self, line: str, state: Any) -> tuple[list[Token], Any]:
		tokens: list[Token] = []
		line_len = len(line)
		i = 0

		in_block_comment = bool(state.get("in_block_comment", False))
		in_string = state.get("in_string")

		expect_type_name = False
		expect_function_name = False
		expect_variable_name = False

		while i < line_len:
			if in_block_comment:
				block_end = self.BLOCK_COMMENT_END
				if not block_end:
					in_block_comment = False
					continue

				end = line.find(block_end, i)
				if end == -1:
					tokens.append((i, line_len, "comment"))
					return tokens, {"in_block_comment": True, "in_string": in_string}

				tokens.append((i, end + len(block_end), "comment"))
				i = end + len(block_end)
				in_block_comment = False
				continue

			if in_string is not None:
				end, closed = self.consume_string(line, -1, in_string)
				tokens.append((0, end, "string"))
				i = end
				if not closed:
					return tokens, {"in_block_comment": in_block_comment, "in_string": in_string}
				in_string = None
				continue

			char = line[i]
			if char.isspace():
				i += 1
				continue

			if self.LINE_COMMENT_PREFIX and line.startswith(self.LINE_COMMENT_PREFIX, i):
				tokens.append((i, line_len, "comment"))
				break

			if (
				self.BLOCK_COMMENT_START
				and self.BLOCK_COMMENT_END
				and line.startswith(self.BLOCK_COMMENT_START, i)
			):
				end = line.find(self.BLOCK_COMMENT_END, i + len(self.BLOCK_COMMENT_START))
				if end == -1:
					tokens.append((i, line_len, "comment"))
					return tokens, {"in_block_comment": True, "in_string": in_string}
				tokens.append((i, end + len(self.BLOCK_COMMENT_END), "comment"))
				i = end + len(self.BLOCK_COMMENT_END)
				continue

			if char in self.STRING_QUOTES:
				end, closed = self.consume_string(line, i, char)
				tokens.append((i, end, "string"))
				i = end
				if not closed:
					return tokens, {"in_block_comment": in_block_comment, "in_string": char}
				continue

			if self.ENABLE_COMPILER_DIRECTIVE and self.COMPILER_RE and char == "#":
				match = self.COMPILER_RE.match(line, i)
				if match is not None:
					tokens.append((i, match.end(), "keyword"))
					i = match.end()
					continue

			if self.ENABLE_METADATA and self.METADATA_RE and char == "@":
				match = self.METADATA_RE.match(line, i)
				if match is not None:
					tokens.append((i, match.end(), "constant.builtin"))
					i = match.end()
					continue

			number_match = self.NUMBER_RE.match(line, i)
			if number_match is not None:
				tokens.append((i, number_match.end(), "number"))
				i = number_match.end()
				continue

			identifier_match = self.IDENTIFIER_RE.match(line, i)
			if identifier_match is not None:
				word = identifier_match.group(0)
				end = identifier_match.end()
				token_name: str | None = None

				if expect_function_name:
					token_name = "function"
					expect_function_name = False
				elif expect_type_name:
					token_name = "class"
					expect_type_name = False
				elif expect_variable_name:
					token_name = "variable"
					expect_variable_name = False
				elif word in self.BOOLEAN_LITERALS:
					token_name = "boolean"
				elif word == self.NULL_LITERAL:
					token_name = "constant.builtin"
				elif word in self.KEYWORDS_FLOW:
					token_name = "keyword.return"
				elif word in self.KEYWORDS_CONTROL:
					token_name = "keyword.control"
				elif word in self.KEYWORDS_DECLARATION or word in self.KEYWORDS_MISC:
					token_name = "keyword"
				elif self.next_non_whitespace_char(line, end) == "(":
					token_name = "function.call"
				elif self._looks_like_type_name(word):
					previous_char = self.previous_non_whitespace_char(line, i)
					if previous_char in {":", "<", ",", "(", "["}:
						token_name = "type"

				if token_name is not None:
					tokens.append((i, end, token_name))

				if word == self.FUNCTION_DECLARATION_KEYWORD:
					expect_function_name = True
				elif word in self.TYPE_EXPECTING_KEYWORDS:
					expect_type_name = True
				elif word in self.VARIABLE_DECLARATION_KEYWORDS:
					expect_variable_name = True

				i = end
				continue

			matched_operator = False
			for operator in self.OPERATORS:
				if line.startswith(operator, i):
					tokens.append((i, i + len(operator), "keyword.operator"))
					i += len(operator)
					matched_operator = True
					break
			if matched_operator:
				continue

			if char in self.SINGLE_OPERATORS:
				tokens.append((i, i + 1, "keyword.operator"))
				i += 1
				continue

			if char in self.PUNCTUATION:
				tokens.append((i, i + 1, "punctuation"))
				i += 1
				continue

			i += 1

		return tokens, {"in_block_comment": in_block_comment, "in_string": in_string}

	def theme_styles(self) -> dict[str, Style]:
		return dict(self.THEME_STYLES)

	@staticmethod
	def _looks_like_type_name(word: str) -> bool:
		return len(word) > 0 and word[0].isupper()
