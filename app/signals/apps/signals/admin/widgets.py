# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.contrib.gis.forms import OSMWidget


class AdminOSMWidget(OSMWidget):
    template_name = 'admin/signals/area/openlayers.html'

    class Media:
        js = ('signals/js/admin-osm-widget.js',)
