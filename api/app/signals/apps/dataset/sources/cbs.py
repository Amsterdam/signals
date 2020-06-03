import os
import zipfile
import time

import requests

from django.db import transaction

from signals.apps.dataset.base import AreaLoader
from signals.apps.signals.models import Area, AreaType
from django.contrib.gis.geos import MultiPolygon

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal import OGRGeomType

from urllib.parse import urlsplit
from tempfile import TemporaryDirectory


class CBSBoundariesLoader(AreaLoader):
    """
    Load municipal (and neigbhorhood) boundaries as SIA Area instances.
    """
    DATASET_URL = 'https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/wijk-en-buurtstatistieken/wijkbuurtkaart_2019_v1.zip'  # noqa

    # Unfortunately, these filenames are not uniformly named over the years,
    # so a hard-coded mapping is provided for the most recent data file (as of
    # this writing 2019).
    DATA_FILES = {
        'cbs-gemeente-2019': 'gemeente_2019_v1.shp',
        # 'cbs-wijk-2019': 'wijk_2019_v1.shp',
        # 'cbs-buurt-2019': 'buurt_2019_v1.shp',
    }

    PROVIDES = ['cbs-gemeente-2019']

    def __init__(self, type_string):
        assert type_string in self.PROVIDES

        self.area_type, _ = AreaType.objects.get_or_create(
            name=type_string,
            code=type_string,
            description=f'{type_string} from CBS "Wijk- en buurtkaart" data.',
        )
        self.data_file = self.DATA_FILES[type_string]

    def _download(self, zip_fullpath):
        """
        Download relevant data file.
        """
        with requests.get(self.DATASET_URL, stream=True) as r:
            r.raise_for_status()
            with open(zip_fullpath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def _unzip(self, temp_dir, zip_fullpath):
        """
        Extract ZIP file to temp_dir.
        """
        print(os.listdir(temp_dir))
        with zipfile.ZipFile(zip_fullpath, 'r') as zf:
            zf.extractall(path=temp_dir)

    def _load_cbs_gemeente(self, data_fullpath):
        """
        Load municipal boundaries.
        """
        ds = DataSource(data_fullpath)
        geom_by_code = {}
        name_by_code = {}

        polygon_type = OGRGeomType('Polygon')
        multipolygon_type = OGRGeomType('MultiPolygon')

        # Collect possible separate geometries representing the area of a signle
        # municipality.
        for feature in ds[0]:
            gm_code = feature.get('GM_CODE')
            name_by_code[gm_code] = feature.get('GM_NAAM')

            # Transform to WGS84 and merge if needed.
            transformed = feature.geom.transform('WGS84', clone=True)
            if gm_code in geom_by_code:
                geom_by_code[gm_code].union(transformed)
            else:
                geom_by_code[gm_code] = transformed

        # Remove previously imported data, save our merged and transformed
        # municipal boundaries to SIA DB.
        with transaction.atomic():
            Area.objects.filter(_type=self.area_type).delete()

            for gm_code, geometry in geom_by_code.items():
                if geometry.geom_type == polygon_type:
                    geos_polygon = geometry.geos
                    geos_geometry = MultiPolygon(geos_polygon)
                elif geometry.geom_type == multipolygon_type:
                    geos_geometry = geometry.geos
                else:
                    raise Exception('Expected either polygon or multipolygon.')

                Area.objects.create(
                    name=name_by_code[gm_code],
                    code=gm_code,  # For now we use the CBS codes
                    _type=self.area_type,
                    geometry=geos_geometry
                )

    def load(self):
        split_url = urlsplit(self.DATASET_URL)
        zip_name = os.path.split(split_url.path)[-1]

        with TemporaryDirectory() as temp_dir:
            zip_fullpath = os.path.join(temp_dir, zip_name)
            data_fullpath = os.path.join(temp_dir, self.data_file)

            self._download(zip_fullpath)
            self._unzip(temp_dir, zip_fullpath)
            self._load_cbs_gemeente(data_fullpath)
