import logging

from requests import get
from requests.exceptions import RequestException

from signals.apps.api.app_settings import SIGNALS_API_ATLAS_SEARCH_URL
from signals.apps.api.v1.validation.address.base import (
    AddressValidationUnavailableException,
    BaseAddressValidation
)

logger = logging.getLogger(__name__)


class AddressValidation(BaseAddressValidation):
    address_validation_url = f'{SIGNALS_API_ATLAS_SEARCH_URL}/adres'

    def _address_dict_to_string(self, address):
        """ Returns a search string as understood by the atlas search. Expects dict in the same
        format as validate_address_dict """

        assert 'huisnummer' in address
        assert 'openbare_ruimte' in address

        return f'{address["openbare_ruimte"]} ' \
               f'{address["huisnummer"]}{address["huisletter"] if "huisletter" in address else ""}' \
               f'{"-" + address["huisnummer_toevoeging"] if "huisnummer_toevoeging" in address else ""}'

    def _search(self, address, *args, **kwargs):
        try:
            response = get(self.address_validation_url, params={'q': self._address_dict_to_string(address)})
            response.raise_for_status()
        except RequestException as e:
            raise AddressValidationUnavailableException(e)
        return response.json()["results"]

    def _search_result_to_address(self, result):
        mapping = {
            'straatnaam': 'openbare_ruimte',
            'postcode': 'postcode',
            'huisnummer': 'huisnummer',
            'bag_huisletter': 'huisletter',
            'bag_toevoeging': 'huisnummer_toevoeging',
            'woonplaats': 'woonplaats',
        }

        sia_address_dict = {}
        for atlas_key, bag_key in mapping.items():
            sia_address_dict[bag_key] = result[atlas_key]
        return sia_address_dict
