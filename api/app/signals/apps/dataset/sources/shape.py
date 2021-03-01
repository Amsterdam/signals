import os
import zipfile
from urllib.parse import urlsplit

import requests
from django.contrib.gis.gdal import DataSource, OGRGeomType
from django.contrib.gis.geos import MultiPolygon
from django.db import transaction

from signals.apps.dataset.base import AreaLoader
from signals.apps.signals.models import Area, AreaType


class ShapeBoundariesLoader(AreaLoader):
    DATASET_INFO = {
        'GENERIC': {}
    }

    PROVIDES = DATASET_INFO.keys()

    def __init__(self, **options):
        type_string = options['type_string']
        directory = options['dir']
        assert type_string in self.PROVIDES

        self.area_type, _ = AreaType.objects.get_or_create(
            name=options['type'],
            code=options['type'],
            description=f"{options['type']} data",
        )
        self.directory = directory  # Data downloaded / processed here. Caller is responsible to clean-up directory.
        self.DATASET_URL = options['url']
        self.data_file = options['shp']
        self.code_field = options['code']
        self.name_field = options['name']

    def _download(self, zip_fullpath):
        """
        Download relevant data file.
        """
        if os.path.exists(zip_fullpath):
            return  # Datafile already downloaded.

        with requests.get(self.DATASET_URL, stream=True, verify=False) as r:
            r.raise_for_status()
            with open(zip_fullpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def _unzip(self, zip_fullpath):
        """
        Extract ZIP file to temp_dir.
        """
        with zipfile.ZipFile(zip_fullpath, 'r') as zf:
            zf.extractall(path=self.directory)

    def _load_shape_data(self, data_fullpath):
        """
        Load shape area as specified area type from the CBS (or compatible format) shapefiles.
        """
        ds = DataSource(data_fullpath)
        geom_by_code = {}
        name_by_code = {}

        polygon_type = OGRGeomType('Polygon')
        multipolygon_type = OGRGeomType('MultiPolygon')

        # Collect possible separate geometries representing the area of a single
        # municipality.
        for feature in ds[0]:
            code = feature.get(self.code_field)
            name_by_code[code] = feature.get(self.name_field)

            # Transform to WGS84 and merge if needed.
            transformed = feature.geom.transform('WGS84', clone=True)
            if code in geom_by_code:
                geom_by_code[code] = geom_by_code[code].union(transformed)
            else:
                geom_by_code[code] = transformed

        # Remove previously imported data, save our merged and transformed boundaries to the DB.
        with transaction.atomic():
            Area.objects.filter(_type=self.area_type).delete()

            for code, geometry in geom_by_code.items():
                if geometry.geom_type == polygon_type:
                    geos_polygon = geometry.geos
                    geos_geometry = MultiPolygon(geos_polygon)
                elif geometry.geom_type == multipolygon_type:
                    geos_geometry = geometry.geos
                else:
                    raise Exception('Expected either polygon or multipolygon.')

                Area.objects.create(
                    name=name_by_code[code],
                    code=code,
                    _type=self.area_type,
                    geometry=geos_geometry
                )

    def load(self):
        split_url = urlsplit(self.DATASET_URL)
        zip_name = os.path.split(split_url.path)[-1]

        zip_fullpath = os.path.join(self.directory, zip_name)
        data_fullpath = os.path.join(self.directory, self.data_file)

        self._download(zip_fullpath)
        self._unzip(zip_fullpath)
        self._load_shape_data(data_fullpath)
