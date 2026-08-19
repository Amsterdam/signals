# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
import re
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element

from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

# The only URL schemes a link in an email may point to. Anything else is dropped, which covers both
# the schemes that execute code in the browser rendering an email preview (javascript:, data:,
# vbscript:) and the ones that hand the recipient of an email from a municipal sender an action they
# did not ask for, such as sms: or callto:.
#
# tel: is on the list because the email templates themselves use it to link the municipal phone
# number. Reporter supplied text cannot reach this list: the markdown link syntax is escaped out of
# it before it is put in the email context, so it cannot produce a link of any scheme at all.
ALLOWED_LINK_SCHEMES = ('http', 'https', 'mailto', 'tel')

# The attribute holding a URL, per element that can carry one.
URL_ATTRIBUTES = {'a': 'href', 'img': 'src'}

# Characters that a browser or mail client throws away before it decides which scheme a URL has,
# which makes them a way to hide one: ' javascript:alert(1)' and 'java\tscript:alert(1)' both run.
# Removing them here means the scheme we check is the scheme that ends up being used.
IGNORED_URL_CHARACTERS = re.compile(r'[\x00-\x20\x7f]')


def is_allowed_url(url: str) -> bool:
    """Determine whether a URL may be used as the destination of a link or an image.

    Parameters
    ----------
    url: str
        The URL as it appears in the rendered markdown.

    Returns
    -------
    bool
        True if the URL has no scheme, or a scheme on the allowlist.
    """
    try:
        scheme = urlsplit(IGNORED_URL_CHARACTERS.sub('', url)).scheme
    except ValueError:
        # A URL we cannot even parse is not one to put in an email.
        return False

    # A URL without a scheme is relative, and so cannot select a protocol handler.
    return not scheme or scheme.lower() in ALLOWED_LINK_SCHEMES


class LinkSchemeTreeprocessor(Treeprocessor):
    """Strips the destination of every link and image that points at a scheme outside the
    allowlist, leaving the text of the link itself untouched."""

    def run(self, root: Element) -> None:
        for element in root.iter():
            attribute = URL_ATTRIBUTES.get(element.tag)
            if attribute is None:
                continue

            url = element.get(attribute)
            if url is not None and not is_allowed_url(url):
                del element.attrib[attribute]


class LinkSchemeExtension(Extension):
    """Restricts the links and images a markdown document may produce to an allowlist of URL
    schemes.

    The markdown library does not filter link destinations at all, so without this extension any
    scheme a reporter or an email template puts between the parentheses of a markdown link ends up
    as the href of a real link: in the email that is sent from a DKIM signed municipal sender, and
    in the rendered email preview shown in the backoffice, where the browser will honour it.

    Filtering here, on the rendered output, rather than on the source text is deliberate. It is the
    last step before the HTML leaves us, so it catches every link regardless of which markdown
    construct produced it: inline links, reference links, autolinks and images all end up in this
    same element tree.
    """

    def extendMarkdown(self, md: Markdown) -> None:
        # A negative priority puts this after every built in treeprocessor, so it sees the tree as
        # it will be serialized: after 'inline' (20) has turned markdown link syntax into elements,
        # and after 'unescape' (0) has resolved backslash escapes inside the destinations.
        md.treeprocessors.register(LinkSchemeTreeprocessor(md), 'link_schemes', -1)
