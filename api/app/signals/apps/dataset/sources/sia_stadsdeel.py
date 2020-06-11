"""
Load handdrawn outline of "Het Amsterdamse Bos" (stored along with the SIA
source), do some spatial queries and store as "SIA stadsdeel" (City District for
SIA purposes).
"""
import os

from django.contrib.gis.db.models.functions import MakeValid
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from django.db import transaction
from django.utils.text import slugify

from signals.apps.dataset.base import AreaLoader
from signals.apps.signals.models import Area, AreaType

THIS_DIR = os.path.dirname(__file__)


class SIAStadsdeelLoader(AreaLoader):
    """
    Load the Amsterdamse Bos geometry as a SIA stadsdeel.

    Note:
    * A "stadsdeel" (city district) in SIA has a slightly different meaning than
      usual. "Het Amsterdamse Bos", a big parkland on the edge of Amsterdam and
      partially located in Amstelveen, also counts as a "stadsdeel" for SIA
      purposes. Similarly, "stadsdeel Zuid" is changed from its usual definition
      to not include any part of "Het Amsterdamse Bos".
    """
    DATAFILE = os.path.join(THIS_DIR, 'amsterdamse_bos.json')
    PROVIDES = ['sia-stadsdeel']

    def __init__(self, type_string, directory=None):
        assert type_string == 'sia-stadsdeel'
        self.area_type, _ = AreaType.objects.get_or_create(
            name='SIA stadsdeel',
            code=type_string,
            description='Stadsdeel volgens de aangepaste definitie in SIA.'
        )

    def _load_amsterdamse_bos_geometry(self):
        """Load the GeoJSON containing Amsterdamse Bos geometry."""
        # Note:
        # * Lacking an official source, we provide our own data file and use
        #   some or our knowledge as to its contents.
        # * We use assert liberally - we cannot recover from an incorrect
        #   datafile, we just fail the import. Since we use DRF in this project
        #   our interpreter is running with assertions on.
        ds = DataSource(self.DATAFILE)
        assert len(ds) == 1
        assert len(ds[0]) == 1
        assert ds[0].srs
        assert ds[0].geom_type == 'MultiPolygon'

        geometries = ds[0].get_geoms(geos=True)
        assert isinstance(geometries[0], MultiPolygon)
        geometries[0].srid = 4326  # Set SRID to WGS84
        return geometries[0]

    def _load_sia_stadsdeel(self):
        """Load "Het Amsterdamse Bos", save it with AreaType "sia-stadsdeel"."""
        geometry = self._load_amsterdamse_bos_geometry()
        assert isinstance(geometry, MultiPolygon)

        with transaction.atomic():
            Area.objects.filter(_type=self.area_type).delete()

            amsterdamse_bos = Area.objects.create(
                name='Het Amsterdamse Bos',
                code='het-amsterdamse-bos',
                _type=self.area_type,
                geometry=geometry
            )
            # Fix invalid geometry
            Area.objects.filter(id=amsterdamse_bos.id).update(geometry=MakeValid('geometry'))

            # Convert al normal stadsdeel instances into SIA stadsdeel instances.
            for entry in Area.objects.filter(_type__code='stadsdeel').exclude(name__iexact='zuid'):
                entry.pk = None
                entry._type = self.area_type
                entry.code = slugify(entry.name)
                entry.save()

            # Special case: subract "Het Amsterdamse Bos" from "Stadsdeel Zuid".
            zuid = Area.objects.get(_type__code='stadsdeel', name__iexact='zuid')
            amsterdamse_bos.refresh_from_db()
            diff = zuid.geometry - amsterdamse_bos.geometry
            # Only handle non-pathological cases. We want the difference between Zuid
            # and the hand drawn Amsterdamse Bos GeoJSON to be either a Polygon or a
            # MultiPolygon. If the difference is empty, a line or a point it cannot
            # serve as an Area in SIA.
            assert diff.geom_typeid in [3, 6]
            if diff.geom_typeid == 3:
                diff = MultiPolygon([diff])

            Area.objects.create(
                name='Zuid',
                code='zuid',
                _type=self.area_type,
                geometry=diff
            )

            # Special case for Weesp (we want it as a sia-stadsdeel as well)
            weesp = Area.objects.get(_type__code='cbs-gemeente-2019', name__iexact='weesp')
            Area.objects.create(
                name='Weesp',
                code='weesp',
                _type=self.area_type,
                geometry=weesp.geometry
            )

    def load(self):
        self._load_sia_stadsdeel()
