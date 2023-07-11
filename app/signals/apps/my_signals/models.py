# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam
from datetime import timedelta

from django.db import models
from django.utils.timezone import now

from signals.apps.my_signals.app_settings import MY_SIGNALS_TOKEN_EXPIRES_SECOND
from signals.apps.signals.tokens.token_generator import TokenGenerator


class Token(models.Model):
    """
    Based on the AuthToken implementation of rest-framework
    """
    key = models.CharField(max_length=120, primary_key=True)
    reporter_email = models.EmailField()
    expires_at = models.DateTimeField(editable=False)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    def __str__(self) -> str:
        return self.key

    @classmethod
    def generate_key(cls) -> str:
        generate = TokenGenerator()
        return generate()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        self.expires_at = now() + timedelta(seconds=MY_SIGNALS_TOKEN_EXPIRES_SECOND)
        return super().save(*args, **kwargs)
