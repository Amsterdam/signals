import os
import zipfile
from urllib.parse import urlsplit

import requests
from django.contrib.gis.gdal import DataSource, OGRGeomType
from django.contrib.gis.geos import MultiPolygon
from django.db import transaction

from signals.apps.dataset.base import AreaLoader
from signals.apps.signals.models import Area, AreaType


class CBSBoundariesLoader(AreaLoader):
    """
    Load municipal (and neigbhorhood) boundaries as SIA Area instances.
    """
    DATASET_URL = 'https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/wijk-en-buurtstatistieken/wijkbuurtkaart_2019_v1.zip'  # noqa

    # Unfortunately, these filenames are not uniformly named over the years,
    # so a hard-coded mapping is provided for the most recent data file (as of
    # this writing 2019).
    DATASET_INFO = {
        'cbs-gemeente-2019': {
            'shp_file': 'gemeente_2019_v1.shp',
            'code_field': 'GM_CODE',
            'name_field': 'GM_NAAM',
        },
        'cbs-wijk-2019': {
            'shp_file': 'wijk_2019_v1.shp',
            'code_field': 'WK_CODE',
            'name_field': 'WK_NAAM',
        },
        'cbs-buurt-2019': {
            'shp_file': 'buurt_2019_v1.shp',
            'code_field': 'BU_CODE',
            'name_field': 'BU_NAAM',
        }
    }

    PROVIDES = DATASET_INFO.keys()

    def __init__(self, type_string, directory):
        assert type_string in self.PROVIDES

        self.area_type, _ = AreaType.objects.get_or_create(
            name=type_string,
            code=type_string,
            description=f'{type_string} from CBS "Wijk- en buurtkaart" data.',
        )
        self.directory = directory  # Data downloaded / processed here. Caller is responsible to clean-up directory.

        dataset_info = self.DATASET_INFO[type_string]
        self.data_file = dataset_info['shp_file']
        self.code_field = dataset_info['code_field']
        self.name_field = dataset_info['name_field']

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

    def _load_cbs_data(self, data_fullpath):
        """
        Load "gemeente", "wijk" or "buurt" areas from the CBS provided shapefiles.
        """
        ds = DataSource(data_fullpath)
        geom_by_code = {}
        name_by_code = {}

        polygon_type = OGRGeomType('Polygon')
        multipolygon_type = OGRGeomType('MultiPolygon')

        # Collect possible separate geometries representing the area of a signle
        # municipality.
        for feature in ds[0]:
            code = feature.get(self.code_field)
            name_by_code[code] = feature.get(self.name_field)

            # Transform to WGS84 and merge if needed.
            transformed = feature.geom.transform('WGS84', clone=True)
            if code in geom_by_code:
                geom_by_code[code].union(transformed)
            else:
                geom_by_code[code] = transformed

        # Remove previously imported data, save our merged and transformed
        # municipal boundaries to SIA DB.
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
        self._load_cbs_data(data_fullpath)
