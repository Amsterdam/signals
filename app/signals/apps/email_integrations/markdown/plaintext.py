# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from bs4 import BeautifulSoup, Tag


def strip_markdown_html(html: str) -> str:
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
    text = ''
    previous = None
    for child in element.children:
        if isinstance(child, str) and child != '\n':
            if previous and previous.name == 'br':
                text += child.strip()
            else:
                text += child
        elif isinstance(child, Tag):
            text += _handle_tag(child)

        previous = child

    if element.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'):
        text += '\n\n'
    elif element.name == 'br':
        text += '\n'
    elif element.name == 'img' and 'alt' in element.attrs:
        text += element.attrs['alt']
    elif element.name == 'a' and 'href' in element.attrs:
        text += f" {element.attrs['href']}"

    return text


def _handle_list(list_element: Tag, indent: int = 0) -> str:
    text = ''
    has_paragraph = False
    for list_item in list_element.contents:
        if isinstance(list_item, Tag):
            text += f'{" " * indent}- '

            has_nested_list = False
            has_paragraph = False
            for child in list_item.contents:
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

    if indent == 0 and not has_paragraph:
        text += '\n'

    return text
