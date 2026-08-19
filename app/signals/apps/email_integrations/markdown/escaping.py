# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
# The characters that let markdown link syntax start. The backslash comes first because it is the
# escape character itself: escaping it after the brackets would escape the backslashes just added.
MARKDOWN_LINK_CHARACTERS = ('\\', '[', ']')


def escape_markdown_link_syntax(text: str) -> str:
    """Escape the markdown constructs that turn text into a link or an image.

    The text a reporter types is not markdown, but it is placed inside a markdown email template,
    which means '[Bel ons](tel:0900-1234)' in a report becomes a link the recipient of the email can
    tap. Escaping the brackets leaves that text completely readable, so the reporter still gets
    their own words quoted back, while making sure none of it can carry a destination.

    Only the link characters are escaped. Emphasis and heading markers cannot point anywhere, and
    escaping those would put a backslash in front of the punctuation of every ordinary sentence.

    Note that the angle brackets of an autolink ('<tel:0900-1234>') and of raw HTML are not escaped
    here: those are already HTML escaped further down the line, by the markdown template filter for
    the HTML email and by the link scheme allowlist for both emails.

    Parameters
    ----------
    text: str
        The text as the reporter submitted it.

    Returns
    -------
    str
        The same text, with the markdown link characters escaped.
    """
    for character in MARKDOWN_LINK_CHARACTERS:
        text = text.replace(character, f'\\{character}')

    return text
