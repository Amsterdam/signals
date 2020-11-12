from mistune.renderers import BaseRenderer


class PlaintextRenderer(BaseRenderer):
    """
    A plaintext renderer that can be used to strip Markdown from a document
    """

    NAME = 'plaintext'
    IS_TREE = False

    def text(self, text):
        return text

    def link(self, link, text=None, title=None):
        return text

    def image(self, src, alt='', title=None):
        return alt

    def emphasis(self, text):
        return text

    def strong(self, text):
        return text

    def codespan(self, text):
        return text

    def linebreak(self):
        return '\n'

    def inline_html(self, html):
        return ''

    def paragraph(self, text):
        return '{}\n\n'.format(text)

    def heading(self, text, level):
        return '{}\n\n'.format(text)

    def newline(self):
        return ''

    def thematic_break(self):
        return '\n'

    def block_text(self, text):
        return text

    def block_code(self, code, info=None):
        return '{}\n'.format(code)

    def block_quote(self, text):
        return '{}\n'.format(text)

    def block_html(self, html):
        return ''

    def block_error(self, html):
        return '{}\n'.format(html)

    def list(self, text, ordered, level, start=None):
        return '{}'.format(text)

    def list_item(self, text, level):
        return '- {}\n'.format(text)
