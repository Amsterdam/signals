# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from urllib.parse import quote

from signals.apps.signals.tokens.token_generator import TokenGenerator


class TestTokenGenerator:
    def test_can_generate_url_safe_token(self):
        generate = TokenGenerator()
        token = generate()

        assert len(token) > 40
        assert quote(token) == token
