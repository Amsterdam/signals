# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.timezone import now

from signals.apps.my_signals.models import Token


class MySignalsTokenAdmin(ModelAdmin):
    list_display = ('is_valid', 'reporter_email', 'key', 'expires_at', 'created_at', )
    search_fields = ('reporter_email', 'key', )

    @admin.display(boolean=True)
    def is_valid(self, obj: Token) -> bool:
        return obj.expires_at > now()


admin.site.register(Token, MySignalsTokenAdmin)
