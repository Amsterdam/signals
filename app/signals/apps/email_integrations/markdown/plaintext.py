# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from bs4 import BeautifulSoup, PageElement, Tag


def strip_markdown_html(html: str) -> str:
    """This function is used to convert the HTML that the markdown
    library produces to plaintext using beautiful soup.

    Parameters
    ----------
    html: str
        The string containing the HTML produced by the markdown library.

    Returns
    -------
    str
        The string containing the HTML that has been converted to plaintext.
    """
    elements = BeautifulSoup(html, features="html.parser")
    text = ''

    for element in elements:
        if isinstance(element, Tag):
            if element.name in ('ol', 'ul'):
                text += _handle_list(element)
            else:
                text += _handle_tag(element)

    return text.strip()


def _handle_tag(element: Tag) -> str:
    """Converts most elements to plaintext output. Lists should not be passed
    to this function as they need to be handled in a different way.

    Parameters
    ----------
    element: Tag
        The element to be converted to plaintext. This element will likely have
        children which can be text, or other (nested) elements.

    Returns
    -------
    str
        The string containing the plaintext equivalent of the element that was provided.
    """
    text = _handle_tag_children(element)

    if element.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'):
        text += '\n\n'
    elif element.name == 'br':
        text += '\n'
    elif element.name == 'img' and 'alt' in element.attrs:
        text += element.attrs['alt']
    elif element.name == 'a' and 'href' in element.attrs:
        text += f" {element.attrs['href']}"

    return text


def _handle_tag_children(element: Tag) -> str:
    """Processes the children of an element. If the child is text, then it will be used directly
    otherwise when a child is an element it will be passed to _handle_tag() to recursively traverse
    through all nested elements.

    Parameters
    ----------
    element: Tag
        The child element to be converted to plaintext.

    Returns
    -------
    str
        The string containing the plaintext equivalent of the element that was provided.
    """
    text = ''

    previous = None
    for child in element.children:
        if isinstance(child, str) and child != '\n':
            if previous and previous.name == 'br':
                text += child.lstrip()
            else:
                text += child
        elif isinstance(child, Tag):
            text += _handle_tag(child)

        previous = child

    return text


def _handle_list(list_element: Tag, indent: int = 0) -> str:
    """Converts list elements <ol> and <ul> to plaintext. All list items will be prefixed with
    a hyphen (-) and optionally add indentation when the list is nested within another list.

    Parameters
    ----------
    list_element: Tag
        The list element to be converted to plaintext. This should always be a <ol> or <ul>
        element.
    indent: int
        The number of spaces to be used for indentation of the list items.

    Returns
    -------
    str
        The plaintext equivalent of the list element.
    """
    text = ''
    has_paragraph = False
    for list_item in list_element.contents:
        if isinstance(list_item, Tag):
            text += f'{" " * indent}- '
            children_text, has_paragraph = _handle_list_item_children(list_item.contents, indent)
            text += children_text

    if indent == 0 and not has_paragraph:
        text += '\n'

    return text


def _handle_list_item_children(contents: list[PageElement], indent: int) -> tuple[str, bool]:
    """Converts the list items to plaintext. It will recurse when a nested list element is
    encountered and when other elements are encountered.

    Parameters
    ----------
    contents: list[PageElement]
        List of the children of a list item element. The children can be either another
        element or a text.
    indent: int
        The amount of space used to indent list items.

    Returns
    -------
    tuple[str, bool]
        The text equivalent of the list item children and if the children contain a
        paragraph.
    """
    text = ''
    has_nested_list = False
    has_paragraph = False
    for child in contents:
        if isinstance(child, Tag):
            if child.name in ('ol', 'ul'):
                text += '\n' + _handle_list(child, indent + 2)
                has_nested_list = True
            else:
                if child.name == 'p':
                    has_paragraph = True
                text += _handle_tag(child)
        elif isinstance(child, str) and child != '\n':
            text += child

    if not has_nested_list and not has_paragraph:
        text += '\n'

    return text, has_paragraph
