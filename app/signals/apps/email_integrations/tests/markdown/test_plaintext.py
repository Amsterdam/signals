# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import os

import markdown

from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html


class TestPlaintextExtension:
    def test_lost_of_markdown(self):
        path = os.path.dirname(os.path.abspath(__file__))
        md = open(os.path.join(path, 'lots_of.md'), 'r').read()
        expected = open(os.path.join(path, 'lots_of.txt'), 'r').read()

        html = markdown.markdown(md, extensions=('legacy_em', ))

        assert expected == strip_markdown_html(html)
