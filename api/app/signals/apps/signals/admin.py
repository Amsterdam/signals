from django.contrib import admin

from .models import Signal


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    pass
