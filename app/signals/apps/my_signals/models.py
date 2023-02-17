# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import binascii
import os
from datetime import timedelta

from django.db import models
from django.utils.timezone import now

from signals.apps.my_signals.app_settings import MY_SIGNALS_TOKEN_EXPIRES_SECOND


class Token(models.Model):
    """
    Based on the AuthToken implementation of rest-framework
    """
    key = models.CharField(max_length=40, primary_key=True)
    reporter_email = models.EmailField()
    expires_at = models.DateTimeField(editable=False)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    def __str__(self):
        return self.key

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        self.expires_at = now() + timedelta(seconds=MY_SIGNALS_TOKEN_EXPIRES_SECOND)
        return super().save(*args, **kwargs)
