from django.http import QueryDict
from requests import get
from requests.exceptions import RequestException

from signals.apps.api.app_settings import SIGNALS_API_PDOK_API_URL
from signals.apps.api.v1.validation.address.base import (
    AddressValidationUnavailableException,
    BaseAddressValidation
)

MUNICIPALITIES = (
    'Amsterdam',
    'Amstelveen',
    'Weesp',
)


class PDOKAddressValidation(BaseAddressValidation):
    address_validation_url = f'{SIGNALS_API_PDOK_API_URL}/locatieserver/v3/suggest'

    def _search_result_to_address(self, result):
        mapping = {
            # PDOK_key: sia_key,
            'straatnaam': 'openbare_ruimte',
            'postcode': 'postcode',
            'huisnummer': 'huisnummer',
            'huisletter': 'huisletter',
            'huisnummertoevoeging': 'huisnummer_toevoeging',
            'woonplaatsnaam': 'woonplaats',
        }

        sia_address_dict = {}
        for PDOK_key, sia_key in mapping.items():
            sia_address_dict[sia_key] = result[PDOK_key] if PDOK_key in result else ''
        return sia_address_dict

    def _pdok_request_query_params(self, address, lon=None, lat=None):
        query_dict = QueryDict(mutable=True)
        query_dict.update({'fl': '*'})
        query_dict.update({'rows': '5'})
        query_dict.update({'fq': 'bron:BAG'})
        query_dict.update({'fq': 'type:adres'})

        if 'woonplaats' in address and address["woonplaats"]:
            query_dict.update({'fq': f'woonplaatsnaam:{address["woonplaats"]}'})
        if 'postcode' in address and address["postcode"]:
            query_dict.update({'fq': f'postcode:{address["postcode"]}'})
        query_dict.update({'fq': f'gemeentenaam:{",".join(MUNICIPALITIES)}'})

        straatnaam = address["openbare_ruimte"]
        huisnummer = address["huisnummer"]
        huisletter = address["huisletter"] if 'huisletter' in address and address["huisletter"] else ''
        toevoeging = f'-{address["huisnummer_toevoeging"]}' if 'huisnummer_toevoeging' in address and address["huisnummer_toevoeging"] else ''  # noqa

        if lon and lat:
            query_dict.update({'lon': lon, 'lat': lat})

        query_dict.update({'q': f'{straatnaam} {huisnummer}{huisletter}{toevoeging}'})
        return query_dict

    def _search(self, address, lon=None, lat=None, *args, **kwargs):
        try:
            query_params = self._pdok_request_query_params(address=address, lon=lon, lat=lat)
            response = get(f'{self.address_validation_url}?{query_params.urlencode()}')
            response.raise_for_status()
        except RequestException as e:
            raise AddressValidationUnavailableException(e)
        return response.json()["response"]["docs"]
