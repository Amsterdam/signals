import requests
from django.contrib.gis.geos import LinearRing, MultiPolygon, Polygon
from django.core.management import BaseCommand
from django.db import transaction
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from signals.apps.signals.models import Area, AreaType


class GebiedenAPIGeometryLoader:
    """Convert not-quite-GeoJSON output from Gebieden API to GEOS geometries."""

    @classmethod
    def load_polygon(cls, rd_coordinates):
        linear_rings = []
        for entry in rd_coordinates:
            lr = LinearRing(entry, srid=28992)
            linear_rings.append(lr)
        return Polygon(*linear_rings, srid=28992)

    @classmethod
    def load_multipolygon(cls, rd_coordinates):
        polygons = []
        for entry in rd_coordinates:
            polygons.append(cls.load_polygon(entry))
        return MultiPolygon(polygons, srid=28992)


class APIGebiedenLoader:
    """
    Load entries from Datapunt "Gebieden API", save as SIA Area instances.
    """
    GEBIEDEN_URL = 'https://api.data.amsterdam.nl/gebieden/{}/'
    CODE_FIELDS = {
        'stadsdeel': 'stadsdeelidentificatie',
        'buurt': 'buurtidentificatie',
        'wijk': 'buurtcombinatie_identificatie',
    }

    def __init__(self, type_string):
        assert type_string in self.CODE_FIELDS

        self.area_type, _ = AreaType.objects.get_or_create(
            name=type_string,
            code=type_string,
            description=f'{type_string} from the Datapunt gebieden API.',
        )
        self.list_endpoint = self.GEBIEDEN_URL.format(type_string)
        self.code_field = self.CODE_FIELDS[type_string]

    def _get_session(self):
        """Create a requests HTTP session with retries."""
        session = requests.session()
        session.mount('https', HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[502, 503, 504]
            )
        ))
        return session

    def _iterate_urls(self, requests_session, url):
        """Extract gebied detail urls from Datapunt Gebieden API list endpoints"""
        next_url = url
        while next_url:
            response = requests_session.get(next_url)
            response_json = response.json()

            for entry in response_json['results']:
                yield entry['_links']['self']['href']

            next_url = response_json['_links']['next']['href']

    def _load_area_detail(self, requests_session, url):
        response = requests_session.get(url)
        response_json = response.json()

        name = response_json['naam']
        code = response_json[self.code_field]  # TODO: consider more appropriate code
        assert response_json['geometrie']['type'] == 'MultiPolygon'
        geometry = GebiedenAPIGeometryLoader.load_multipolygon(
            response_json['geometrie']['coordinates']
        )
        geometry.transform(ct=4326)

        Area.objects.create(
            name=name,
            code=code,
            _type=self.area_type,
            geometry=geometry
        )

    def load(self):
        requests_session = self._get_session()

        with transaction.atomic():
            for detail_url in self._iterate_urls(requests_session, self.list_endpoint):
                self._load_area_detail(requests_session, detail_url)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type_string', type=str, help='stadsdeel, wijk or buurt')

    def handle(self, *args, **options):
        assert 'type_string' in options
        loader = APIGebiedenLoader(options['type_string'])

        self.stdout.write(f'Loading {options["type_string"]} areas from gebieden API...')
        loader.load()
        self.stdout.write('...done.')
