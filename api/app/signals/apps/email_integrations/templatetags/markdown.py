import mistune
from django import template
from django.utils.safestring import mark_safe

from signals.apps.email_integrations.renderers import PlaintextRenderer

render_markdown = mistune.create_markdown(escape=True)
render_plaintext = mistune.create_markdown(renderer=PlaintextRenderer())

register = template.Library()


@register.filter
def markdown(value):
    return mark_safe(render_markdown(value))


@register.filter(is_safe=True)
def plaintext(value):
    return render_plaintext(value)
