# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import markdown
from django import template
from django.utils.safestring import mark_safe

from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html

register = template.Library()


@register.filter
def markdown(value):
    return mark_safe(markdown.markdown(value, extensions=('legacy_em', )))


@register.filter(is_safe=True)
def plaintext(value):
    return strip_markdown_html(markdown.markdown(value, extensions=('legacy_em', )))
