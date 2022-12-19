# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import json

from django.contrib import admin
from django.contrib.gis.admin import GeoModelAdmin
from django.contrib.gis.db.models import JSONField
from django.utils.safestring import mark_safe

from signals.apps.api.forms.widgets import PrettyJSONWidget
from signals.apps.gisib.models import GISIBFeature


class SpeciesDescriptionListFilter(admin.SimpleListFilter):
    title = 'RAW Feature Soortnaam'
    parameter_name = 'rf_sn'

    def lookups(self, request, model_admin):
        return (
            ('quercus', 'Quercus (General)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'quercus':
            return queryset.filter(raw_feature__properties__Soortnaam__Description__istartswith='quercus')
        elif self.value():
            return queryset.filter(raw_feature__properties__Soortnaam__Description__iexact=self.value())


class GISIBFeatureAdmin(GeoModelAdmin):
    search_fields = ('gisib_id',)
    list_display = ('gisib_id', 'object_type', 'latin_name', 'created_at',)
    list_per_page = 20
    list_filter = (SpeciesDescriptionListFilter,)
    sortable_by = ('gisib_id',)

    fields = ('gisib_id', 'geometry', 'properties_pretified', 'raw_feature_prettified',)
    readonly_fields = ('properties_pretified', 'raw_feature_prettified', 'created_at', 'updated_at',)
    modifiable = False

    formfield_overrides = {JSONField: {'widget': PrettyJSONWidget}}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def object_type(self, obj):
        return obj.properties['object']['type']

    def latin_name(self, obj):
        return obj.properties['object']['latin']

    def properties_pretified(self, instance):
        return mark_safe(f'<pre>{json.dumps(instance.properties, sort_keys=True, indent=2)}</pre>')
    properties_pretified.short_description = 'Properties'

    def raw_feature_prettified(self, instance):
        return mark_safe(f'<pre>{json.dumps(instance.raw_feature, sort_keys=True, indent=2)}</pre>')
    raw_feature_prettified.short_description = 'raw GISIB Feature'


admin.site.register(GISIBFeature, GISIBFeatureAdmin)
