from unittest.mock import patch

from django.test import TestCase
from PIL import Image

from signals.apps.signals.utils.map import MapGenerator


class MapGeneratorTest(TestCase):

    def test_tile_calculation(self):
        mg = MapGenerator()
        # nassaulaan, the hague
        x, y = mg.deg2num(lat_deg=52.0870974, lon_deg=4.3075533, zoom=17)
        self.assertEqual(x, 67104)
        self.assertEqual(y, 43243)

        # weesperstraat, amsterdam
        x, y = mg.deg2num(lat_deg=52.3628026, lon_deg=4.9075201, zoom=17)
        self.assertEqual(x, 67322)
        self.assertEqual(y, 43079)

    @patch("signals.apps.signals.utils.map.MapGenerator.load_image")
    def test_make_map(self, load_image):
        load_image.return_value = Image.new("RGBA", (3*256, 3*256), 0)
        try:
            mg = MapGenerator()
            map = mg.make_map(
                url_template="https://geodata.nationaalgeoregister.nl/tiles/service/wmts/brtachtergrondkaart/EPSG:3857/{zoom}/{x}/{y}.png", # noqa
                lat=52.0870974,
                lon=4.3075533,
                zoom=17,
                img_size=[648, 250]
            )
            self.assertIsNotNone(map)
            self.assertEquals(map.size, (648, 250))
        except Exception:
            self.fail('Mapgenerator raised unexpected exception!')
