# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import markdown as md
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html

register = template.Library()


@register.filter
def markdown(value: str) -> str:
    return mark_safe(md.markdown(escape(value)))


@register.filter(is_safe=True)
def plaintext(value: str) -> str:
    return strip_markdown_html(md.markdown(value))
