import io
import urllib.request
from math import asinh, pi, radians, tan

from PIL import Image

TILE_SIZE = 256


#  https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon..2Flat._3
class MapGenerator:
    def _deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = radians(lat_deg)
        n = 2.0 ** zoom
        xtile = (lon_deg + 180.0) / 360.0 * n
        ytile = (1.0 - asinh(tan(lat_rad)) / pi) / 2.0 * n
        return (xtile, ytile)

    def deg2num(self, lat_deg, lon_deg, zoom):
        (xtile, ytile) = self._deg2num(lat_deg, lon_deg, zoom)
        return (int(xtile), int(ytile))

    def deg2num_pixel(self, lat_deg, lon_deg, zoom):
        (xtile, ytile) = self._deg2num(lat_deg, lon_deg, zoom)
        xpixel = int((xtile % 1) * TILE_SIZE)
        ypixel = int((ytile % 1) * TILE_SIZE)
        return (xpixel, ypixel)

    def load_image(self, url_template, zoom, x, y):
        img = Image.new("RGBA", (3*TILE_SIZE, 3*TILE_SIZE), 0)
        try:
            for i in range(-1, 2, 1):
                for j in range(-1, 2, 1):
                    url = url_template.format(zoom=zoom, x=x+i, y=y+j)
                    with urllib.request.urlopen(url) as response:
                        offset = ((i+1) * TILE_SIZE, (j+1) * TILE_SIZE)
                        img.paste(
                            Image.open(io.BytesIO(response.read())),
                            offset
                        )
        except Exception:
            pass  # use empty image in case of errors

        return img

    def _clip_coordinates(self, input):
        rounded = round(input)
        if rounded < 0:
            return 0
        if rounded > 3 * TILE_SIZE:
            return 3 * TILE_SIZE
        return rounded

    def make_map(self, url_template, lat, lon, zoom, img_size):
        (W, H) = img_size
        (x, y) = self.deg2num(lat, lon, zoom)

        img = self.load_image(url_template, zoom, x, y)
        (xp, yp) = self.deg2num_pixel(lat, lon, zoom)

        # left top x
        x1 = (3 * TILE_SIZE - W)/2
        # left bottom x
        x2 = x1 + W

        y1 = (TILE_SIZE + yp) - (H / 2)
        y2 = (TILE_SIZE + yp) + (H / 2)

        # Extract img_size from the larger covering map
        cropped = img.crop((
            self._clip_coordinates(x1),
            self._clip_coordinates(y1),
            self._clip_coordinates(x2),
            self._clip_coordinates(y2),
        ))

        # return cropped image and marker position
        return (cropped, (int(TILE_SIZE + xp - x1), int(TILE_SIZE + yp - y1)))
