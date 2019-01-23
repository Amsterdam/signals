from django.conf import settings
from json import loads
from requests import get
from requests.exceptions import RequestException


class AtlasResultUnavailableException(Exception):
    pass


class NoResultsException(Exception):
    pass


class AddressValidation:
    ATLAS_SEARCH_URL = settings.DATAPUNT_API_URL + 'atlas/search'

    def validate(self, address: str) -> dict:
        results = self._search_atlas(address)

        if len(results) == 0:
            raise NoResultsException()

        return self._atlas_result_to_address(results[0])

    def _search_atlas(self, address: str) -> dict:
        try:
            response = get(self.ATLAS_SEARCH_URL + '/adres', params={'q': address})
            response.raise_for_status()
        except RequestException as e:
            raise AtlasResultUnavailableException(e)

        return loads(response.text)["results"]

    def _atlas_result_to_address(self, address: dict) -> dict:
        mapping = {
            "straatnaam": "openbare_ruimte",
            "postcode": "postcode",
            "huisnummer": "huisnummer",
            "bag_huisletter": "huisletter",
            "bag_toevoeging": "huisnummer_toevoeging",
        }

        result = {}

        for atlas_key, bag_key in mapping.items():
            result[bag_key] = address[atlas_key]

        return result
