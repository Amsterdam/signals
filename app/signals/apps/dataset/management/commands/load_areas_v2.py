import requests
import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from signals.apps.signals.models import AreaType, Area

class Command(BaseCommand):
    help = "Load CBS areas into the database"

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name", required=True, help="Municipality name")
        parser.add_argument("-t", "--type", required=True, help="Area type (wijken or buurten)")
        parser.add_argument("-d", "--delete", action="store_true", required=False, help="If specified, delete former database entries in Area table")

    def handle(self, *args, **options):
        municipality_name = options['name']
        area_type_name = options['type']
        delete = options['delete']

        if delete:
            Area.objects.filter(_type__name='district').delete()

        self.get_pdok_data(municipality_name, area_type_name)

    def get_pdok_data(self, municipality_name, area_type_name):
        url = "https://service.pdok.nl/cbs/wijkenbuurten/2023/wfs/v1_0"

        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typename": f"wijkenbuurten:{area_type_name}",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "filter": f"<Filter><PropertyIsEqualTo><PropertyName>gemeentenaam</PropertyName><Literal>{municipality_name}</Literal></PropertyIsEqualTo></Filter>"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            area_type, _ = AreaType.objects.get_or_create(
                code='district',
                defaults={'name': 'district', 'description': 'data from CBS "Wijk- en buurtkaart" data.'}
            )

            for area in data['features']:
                geojson_str = json.dumps(area['geometry'])

                if area_type_name == "wijken":
                    area_name = area['properties']['wijknaam']
                    area_code = area['properties']['wijkcode']
                elif area_type_name == "buurten":
                    area_name = area['properties']['buurtnaam']
                    area_code = area['properties']['buurtcode']
                else:
                    self.stdout.write(self.style.ERROR(f"Unsupported area type: {area_type_name}"))
                    return

                geometry = GEOSGeometry(geojson_str)

                Area.objects.create(
                    name=area_name,
                    code=area_code,
                    _type=area_type,
                    geometry=geometry
                )

        else:
            self.stdout.write(self.style.ERROR(f"Failed to retrieve data. Status code: {response.status_code}"))