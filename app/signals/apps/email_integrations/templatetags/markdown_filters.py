# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import markdown as md
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from signals.apps.email_integrations.markdown.link_schemes import LinkSchemeExtension
from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html

register = template.Library()


def _render(value: str) -> str:
    """Render markdown to HTML, with the destination of every link and image restricted to an
    allowlist of URL schemes. A new Markdown instance per call, because it is not reusable across
    threads."""
    return md.markdown(value, extensions=[LinkSchemeExtension()])


@register.filter
def markdown(value: str) -> str:
    return mark_safe(_render(escape(value)))


@register.filter(is_safe=True)
def plaintext(value: str) -> str:
    return strip_markdown_html(_render(value))
