"""
Load handdrawn outline of "Het Amsterdamse Bos" (stored along with the SIA
source) and do some spatial queries
"""
import os

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon

from signals.apps.signals.models import Area, AreaType

THIS_DIR = os.path.dirname(__file__)
DATAFILE = os.path.join(THIS_DIR, 'amsterdamse_bos.json')


def load_amsterdamse_bos():
    area_type, _ = AreaType.objects.get_or_create(
        name='Test gebiedstype',
        code='test',
        description='Throw-away gebiedstype voor tests',
    )

    # We have 1 multipolygon present representing "Het Amsterdamse Bos"
    # geometry, fail if anything else is present.
    ds = DataSource(DATAFILE)
    assert len(ds) == 1
    assert len(ds[0]) == 1
    assert ds[0].geom_type == 'MultiPolygon'

    geometries = ds[0].get_geoms(geos=True)
    assert isinstance(geometries[0], MultiPolygon)

    # Create our Area
    Area.objects.create(
        name='Het Amsterdamse Bos',
        code='het-amsterdamse-bos',
        _type=area_type,
        geometry=geometries[0],
    )
