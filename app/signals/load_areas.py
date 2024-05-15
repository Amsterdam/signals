import requests
import sys

from apps.signals.models import AreaType

# Get municipality data from the PDOK WFS service
def get_municipality_data(municipality_name):
    url = "https://service.pdok.nl/cbs/wijkenbuurten/2023/wfs/v1_0"
    type_string = "gemeente"

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typename": "wijkenbuurten:gemeenten",
        "outputFormat": "application/json",
        "maxFeatures": 10,
        "filter": f"<Filter><PropertyIsEqualTo><PropertyName>gemeentenaam</PropertyName><Literal>{municipality_name}</Literal></PropertyIsEqualTo></Filter>"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        AreaType.objects.get_or_create(
            code=type_string,
            defaults={'name': type_string, 'description': f'{type_string} from CBS "Wijk- en buurtkaart" data.'}
        )

        print(data['features'])
    else:
        print("Failed to retrieve data. Status code:", response.status_code)


# When executing this script you have to give a Dutch municipality name as argument, if you did this we will execute
# get_municipality_data()
def load_cbs_areas():
    if len(sys.argv) != 2:
        print("Usage: python3 file.py <municipality_name>")
        return

    municipality_name = sys.argv[1]
    get_municipality_data(municipality_name)


if __name__ == "__main__":
    load_cbs_areas()
