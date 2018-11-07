from django.contrib import admin

from signals.apps.zds.models import ZaakDocument, ZaakSignal


@admin.register(ZaakSignal)
class ZaakSignalAdmin(admin.ModelAdmin):
    pass


@admin.register(ZaakDocument)
class ZaakDocumentAdmin(admin.ModelAdmin):
    pass
