# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
import re
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

ALLOWED_SCHEMES = ('http', 'https', 'mailto')

# The attribute holding a URL, per element that can carry one.
URL_ATTRIBUTES = {'a': 'href', 'img': 'src'}

# Characters a browser throws away before it decides which scheme a URL has, which makes them a way
# to hide one: ' javascript:alert(1)' and 'java\tscript:alert(1)' both run.
HIDDEN_SCHEME_CHARACTERS = re.compile(r'[\x00-\x20\x7f]')


def is_allowed_url(url: str) -> bool:
    """A URL may be a destination if it is relative, or if its scheme is on the allowlist."""
    try:
        scheme = urlsplit(HIDDEN_SCHEME_CHARACTERS.sub('', url)).scheme
    except ValueError:
        return False  # A URL we cannot even parse is not one to put in an email.

    return not scheme or scheme.lower() in ALLOWED_SCHEMES


class LinkSchemeTreeprocessor(Treeprocessor):
    def run(self, root: Element) -> None:
        for element in root.iter():
            attribute = URL_ATTRIBUTES.get(element.tag)
            if attribute and not is_allowed_url(element.get(attribute, '')):
                del element.attrib[attribute]


class LinkSchemeExtension(Extension):
    """Limit the links and images a markdown document produces to an allowlist of URL schemes.

    The markdown library does not filter link destinations, so without this any scheme a reporter
    or an email template puts between the parentheses of a markdown link becomes a real href: in
    the email sent from a DKIM signed municipal sender, and in the email preview in the backoffice,
    where the browser will honour it.

    Filtering the rendered output rather than the source text catches every link regardless of the
    markdown that produced it: inline links, reference links, autolinks and images all end up in
    this same element tree.
    """

    def extendMarkdown(self, md: Markdown) -> None:
        # Runs after every built in treeprocessor, so it sees the tree that gets serialized.
        md.treeprocessors.register(LinkSchemeTreeprocessor(md), 'link_schemes', -1)
