# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import io
from unittest.mock import patch

from django.test import TestCase
from PIL import Image

from signals.apps.services.domain.wmts_map_generator import WMTSMapGenerator


class WMTSMapGeneratorTest(TestCase):

    def test_tile_calculation(self):
        # nassaulaan, the hague
        x, y = WMTSMapGenerator.deg2num(lat_deg=52.0870974, lon_deg=4.3075533, zoom=17)
        self.assertEqual(x, 67104)
        self.assertEqual(y, 43243)

        # weesperstraat, amsterdam
        x, y = WMTSMapGenerator.deg2num(lat_deg=52.3628026, lon_deg=4.9075201, zoom=17)
        self.assertEqual(x, 67322)
        self.assertEqual(y, 43079)

    @patch("urllib.request.urlopen")
    def test_make_map(self, urlopen):
        tile_img = Image.new("RGBA", (256, 256), 0)
        png_array = io.BytesIO()
        tile_img.save(png_array, format='png')
        urlopen.return_value.__enter__.return_value.read.return_value = png_array.getvalue()

        try:
            map = WMTSMapGenerator.make_map(
                url_template="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png", # noqa
                lat=52.0870974,
                lon=4.3075533,
                zoom=17,
                img_size=[648, 250]
            )
            self.assertIsNotNone(map)
            self.assertEqual(map.size, (648, 250))
        except Exception:
            self.fail('Mapgenerator raised unexpected exception!')
