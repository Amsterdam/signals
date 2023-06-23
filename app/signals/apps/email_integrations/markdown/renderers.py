# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from typing import Any

from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer


class PlaintextRenderer(MarkdownRenderer):
    """
    A plaintext renderer that can be used to strip Markdown from a document
    """
    NAME = 'plaintext'

    def link(self, token: dict[str, Any], state: BlockState) -> str:
        text = self.render_children(token, state)
        return f"{text} {token['attrs']['url']}"

    def image(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def emphasis(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def strong(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def heading(self, token: dict[str, Any], state: BlockState) -> str:
        text = self.render_children(token, state)
        return text + '\n\n'

    def block_quote(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def list(self, token: dict[str, Any], state: BlockState) -> str:
        attrs = token['attrs']
        if not attrs['ordered']:
            token['bullet'] = '-'

        return super().list(token, state)

    def thematic_break(self, token: dict[str, Any], state: BlockState) -> str:
        return '-----------------------------------------------------------\n\n'

    def block_code(self, token: dict[str, Any], state: BlockState) -> str:
        return token['raw'] + '\n\n'

    def codespan(self, token: dict[str, Any], state: BlockState) -> str:
        return '"' + token['raw'] + '"'

    def block_html(self, token: dict[str, Any], state: BlockState) -> str:
        return ''

    def inline_html(self, token: dict[str, Any], state: BlockState) -> str:
        return ''
