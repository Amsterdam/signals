# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.test import SimpleTestCase

from signals.apps.signals.admin.widgets import AdminOSMWidget


class TestAdminOSMWidget(SimpleTestCase):
    def test_renders_without_inline_script(self):
        widget = AdminOSMWidget()

        html = widget.render('geometry', None, attrs={'id': 'id_geometry'})

        self.assertIn('data-admin-osm-widget', html)
        self.assertNotIn('<script', html)

    def test_loads_openlayers_dependencies_and_initializer(self):
        widget = AdminOSMWidget()

        self.assertEqual(
            widget.media._js[0],
            'https://cdn.jsdelivr.net/npm/ol@v7.2.2/dist/ol.js',
        )
        self.assertIn('gis/js/OLMapWidget.js', widget.media._js)
        self.assertIn('signals/js/admin-osm-widget.js', widget.media._js)
