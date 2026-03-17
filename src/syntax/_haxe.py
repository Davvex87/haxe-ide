from __future__ import annotations

from typing import ClassVar

from syntax.bases import CodeSyntaxStyle


class HaxeSyntaxStyle(CodeSyntaxStyle):
	MODE: ClassVar[str] = "haxe"

	KEYWORDS_DECLARATION: ClassVar[set[str]] = {
		"class",
		"interface",
		"enum",
		"typedef",
		"abstract",
		"function",
		"var",
		"final",
		"package",
		"import",
		"using",
		"macro",
	}

	KEYWORDS_CONTROL: ClassVar[set[str]] = {
		"if",
		"else",
		"switch",
		"case",
		"default",
		"for",
		"while",
		"do",
		"try",
		"catch",
	}

	KEYWORDS_FLOW: ClassVar[set[str]] = {
		"return",
		"break",
		"continue",
		"throw",
	}

	KEYWORDS_MISC: ClassVar[set[str]] = {
		"extends",
		"implements",
		"new",
		"cast",
		"in",
		"untyped",
		"inline",
		"public",
		"private",
		"static",
		"override",
		"dynamic",
	}

	BOOLEAN_LITERALS: ClassVar[set[str]] = {"true", "false"}
	TYPE_EXPECTING_KEYWORDS: ClassVar[set[str]] = {
		"class",
		"interface",
		"enum",
		"typedef",
		"abstract",
		"extends",
		"implements",
		"new",
		"cast",
	}