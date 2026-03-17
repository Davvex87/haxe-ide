from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import ClassVar

from textual._text_area_theme import TextAreaTheme
from textual.widgets import TextArea

from syntax import (
	HaxeSyntaxStyle,
	JsonSyntaxStyle,
	SyntaxStyle
)


class CodeArea(TextArea):
	"""A TextArea that delegates syntax tokenization to language modules.

	This fallback highlighter runs without tree-sitter and maps token categories
	to theme capture names, so the same palette strategy can be reused later with
	tree-sitter queries.
	"""

	_THEME_NAME: ClassVar[str] = "haxe_ide"

	def __init__(self, *args, **kwargs):
		kwargs.pop("language", None)
		super().__init__(*args, language=None, **kwargs)
		self._syntax_styles: dict[str, SyntaxStyle] = {
			"haxe": HaxeSyntaxStyle(),
			"json": JsonSyntaxStyle(),
		}
		self._syntax_mode = "haxe"
		self._register_editor_theme()

	def on_mount(self) -> None:
		self._refresh_highlights_for_mode()

	def on_text_area_changed(self, event: TextArea.Changed) -> None:
		if event.text_area is self:
			self._refresh_highlights_for_mode()

	def set_syntax_mode(self, mode: str) -> None:
		self._syntax_mode = mode
		self._refresh_highlights_for_mode()

	def _refresh_highlights_for_mode(self) -> None:
		syntax_style = self._syntax_styles.get(self._syntax_mode)
		if syntax_style is None:
			self._clear_manual_highlights()
			return

		self._refresh_highlights(syntax_style)

	def _refresh_highlights(self, syntax_style: SyntaxStyle) -> None:
		line_highlights: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
		state = syntax_style.initial_state()

		for line_index, line in enumerate(self.document.lines):
			tokens, state = syntax_style.tokenize_line(line, state)
			if not tokens:
				continue

			byte_offsets = self._char_to_byte_offsets(line)
			for start, end, token_name in tokens:
				if end > start:
					line_highlights[line_index].append(
						(byte_offsets[start], byte_offsets[end], token_name)
					)

		self._highlights.clear()
		self._highlights.update(line_highlights)
		self._line_cache.clear()
		self.refresh()

	def _clear_manual_highlights(self) -> None:
		if self._highlights:
			self._highlights.clear()
			self._line_cache.clear()
			self.refresh()

	@staticmethod
	def _char_to_byte_offsets(line: str) -> list[int]:
		offsets = [0]
		byte_offset = 0
		for char in line:
			byte_offset += len(char.encode("utf-8"))
			offsets.append(byte_offset)
		return offsets

	def _register_editor_theme(self) -> None:
		base_theme = TextAreaTheme.get_builtin_theme("css")
		if base_theme is None:
			return

		syntax_styles = dict(base_theme.syntax_styles)
		for syntax_style in self._syntax_styles.values():
			syntax_styles.update(syntax_style.theme_styles())

		theme = replace(base_theme, name=self._THEME_NAME, syntax_styles=syntax_styles)
		self.register_theme(theme)
		self.theme = self._THEME_NAME
