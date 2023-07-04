# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from django.http import QueryDict
from requests import get
from requests.exceptions import RequestException

from signals.apps.api.validation.address.base import (
    AddressValidationUnavailableException,
    BaseAddressValidation
)
from signals.settings import DEFAULT_PDOK_MUNICIPALITIES, PDOK_LOCATIESERVER_SUGGEST_ENDPOINT


class PDOKAddressValidation(BaseAddressValidation):
    address_validation_url = PDOK_LOCATIESERVER_SUGGEST_ENDPOINT

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

        if 'woonplaats' in address and address['woonplaats'].strip():
            query_dict.update({'fq': f'woonplaatsnaam:{address["woonplaats"].strip()}'})
        if 'postcode' in address and address['postcode'].strip():
            query_dict.update({'fq': f'postcode:{address["postcode"].strip()}'})

        # remove '', ' ' strings before formatting
        cleaned_pdok_list = filter(lambda item: item, map(str.strip, DEFAULT_PDOK_MUNICIPALITIES))
        query_dict.update({'fq': f'''gemeentenaam:("{'" "'.join(cleaned_pdok_list)}")'''})

        straatnaam = address['openbare_ruimte'].strip()
        huisnummer = str(address['huisnummer']).strip()
        huisletter = address['huisletter'].strip() if 'huisletter' in address and address['huisletter'] else ''
        toevoeging = f'-{address["huisnummer_toevoeging"].strip()}' if 'huisnummer_toevoeging' in address and address['huisnummer_toevoeging'] else ''  # noqa

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
