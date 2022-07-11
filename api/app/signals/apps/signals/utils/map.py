# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import io
import urllib.request
from math import asinh, modf, pi, radians, tan

from PIL import Image

TILE_SIZE = 256


# CANDIDATE FOR SERVICE
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

    def calc_tiles_in_pixels(self, input, pixels):
        # returns the amount of tiles required to span desired number of pixels
        # skip pixels in own tile
        net_pixels = max(0, pixels - input)
        # determine required number of tiles
        fract_part, int_part = modf(net_pixels / TILE_SIZE)
        return int(int_part) if fract_part == 0 else int(int_part + 1)

    def load_image(self, url_template, zoom, x, y, left, top, right, bottom):
        # potential number of tiles left and right, add one for the tile with the marker
        xtiles = left + right + 1
        # same as above but for top, bottom
        ytiles = top + bottom + 1

        img = Image.new("RGBA", (xtiles*TILE_SIZE, ytiles*TILE_SIZE), 0)
        try:
            for i in range(-left, right + 1, 1):
                for j in range(-top, bottom + 1, 1):
                    url = url_template.format(zoom=zoom, x=x+i, y=y+j)
                    with urllib.request.urlopen(url) as response:
                        offset = ((i+left) * TILE_SIZE, (j+top) * TILE_SIZE)
                        img.paste(Image.open(io.BytesIO(response.read())), offset)
        except Exception:
            pass  # use empty image in case of errors

        return img

    def make_map(self, url_template, lat, lon, zoom, img_size):
        W, H = img_size
        # x and y tiles
        xt, yt = self.deg2num(lat, lon, zoom)
        # x and y pixel positon within tile
        xp, yp = self.deg2num_pixel(lat, lon, zoom)
        tiles_left = self.calc_tiles_in_pixels(xp, W / 2)
        tiles_top = self.calc_tiles_in_pixels(yp, H / 2)
        tiles_right = self.calc_tiles_in_pixels(TILE_SIZE - xp, W / 2)
        tiles_bottom = self.calc_tiles_in_pixels(TILE_SIZE - yp, H / 2)

        img = self.load_image(url_template, zoom, xt, yt, tiles_left, tiles_top, tiles_right, tiles_bottom)

        # marker x and y in new map
        mx = int(tiles_left * TILE_SIZE + xp)
        my = int(tiles_top * TILE_SIZE + yp)

        x1 = int(mx - W / 2)
        x2 = x1 + W

        y1 = int(my - H / 2)
        y2 = y1 + H

        # Extract img_size from the larger covering map
        cropped = img.crop((x1, y1, x2, y2))

        return cropped
