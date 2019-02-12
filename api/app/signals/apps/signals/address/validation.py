from django.conf import settings
from requests import get
from requests.exceptions import RequestException


class AddressValidationUnavailableException(Exception):
    pass


class NoResultsException(Exception):
    pass


class AddressValidation:
    ATLAS_SEARCH_URL = settings.DATAPUNT_API_URL + 'atlas/search'

    def validate_address_string(self, address: str) -> dict:
        results = self._search_atlas(address)

        if len(results) == 0:
            raise NoResultsException()

        return self._atlas_result_to_address(results[0])

    def validate_address_dict(self, address: dict) -> dict:
        """ Expects address dict with the following fields:

        - openbare_ruimte
        - huisnummer
        - huisletter (optional)
        - huisnummer_toevoeging (optional)

        Postcode and woonplaats fields will be ignored (the atlas search does not accept those)
        """
        address_str = self._address_dict_to_string(address)

        return self.validate_address_string(address_str)

    def _address_dict_to_string(self, address: dict) -> str:
        """ Returns a search string as understood by the atlas search. Expects dict in the same
        format as validate_address_dict """

        assert "huisnummer" in address
        assert "openbare_ruimte" in address

        return "{} {}{}{}".format(
            address["openbare_ruimte"],
            address["huisnummer"],
            address["huisletter"] if "huisletter" in address else "",
            ("-" + address["huisnummer_toevoeging"]) if "huisnummer_toevoeging" in address else "",
        )

    def _search_atlas(self, address: str) -> dict:
        try:
            response = get(self.ATLAS_SEARCH_URL + '/adres', params={'q': address})
            response.raise_for_status()
        except RequestException as e:
            raise AddressValidationUnavailableException(e)

        return response.json()["results"]

    def _atlas_result_to_address(self, address: dict) -> dict:
        mapping = {
            "straatnaam": "openbare_ruimte",
            "postcode": "postcode",
            "huisnummer": "huisnummer",
            "bag_huisletter": "huisletter",
            "bag_toevoeging": "huisnummer_toevoeging",
            "woonplaats": "woonplaats",
        }

        result = {}

        for atlas_key, bag_key in mapping.items():
            result[bag_key] = address[atlas_key]

        return result
