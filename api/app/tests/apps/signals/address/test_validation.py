from json import load, dumps
from os.path import abspath, dirname, join
from unittest.mock import MagicMock

from django.conf import settings
from django.test import SimpleTestCase
from requests.exceptions import ConnectionError
from requests_mock.mocker import Mocker

from signals.apps.signals.address.validation import AddressValidation, \
    AtlasResultUnavailableException, NoResultsException


class TestAddressValidation(SimpleTestCase):
    ATLAS_RESPONSE_JSON = "atlas_result.json"
    atlas_response = None
    address = "Weesperstraat 113"

    def _get_file_path(self, relative_file):
        return join(dirname(abspath(__file__)), relative_file)

    def _get_atlas_response(self):
        if self.atlas_response is None:
            with open(self._get_file_path(self.ATLAS_RESPONSE_JSON)) as f:
                self.atlas_response = load(f)

        return self.atlas_response

    def _get_atlas_search_url(self):
        return settings.DATAPUNT_API_URL + 'atlas/search/adres'

    def test_validate_no_results(self):
        address_validation = AddressValidation()

        address_validation._search_atlas = MagicMock(return_value=[])

        self.assertRaises(NoResultsException, address_validation.validate, self.address)

        address_validation._search_atlas.assert_called_with(self.address)

    def test_validate_with_results(self):
        address_validation = AddressValidation()

        atlas_first_result = self._get_atlas_response()["results"][0]

        address_validation._search_atlas = MagicMock(return_value=[atlas_first_result])
        address_validation._atlas_result_to_address = MagicMock()

        address_validation.validate(self.address)

        address_validation._search_atlas.assert_called_with(self.address)
        address_validation._atlas_result_to_address.assert_called_with(atlas_first_result)

    def test_search_atlas_with_unsuccessful_http_code(self):
        address_validation = AddressValidation()

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), status_code=400)

            self.assertRaises(AtlasResultUnavailableException, address_validation._search_atlas,
                              self.address)

    def test_search_atlas_with_connection_error(self):
        address_validation = AddressValidation()

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), exc=ConnectionError)

            self.assertRaises(AtlasResultUnavailableException, address_validation._search_atlas,
                              self.address)

    def test_search_atlas_successful_request(self):
        address_validation = AddressValidation()

        search_result = self._get_atlas_response()
        expected = search_result["results"]

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), text=dumps(search_result))

            self.assertEquals(address_validation._search_atlas(self.address), expected)

    def test_atlas_result_to_address(self):
        address_validation = AddressValidation()

        test_cases = [
            (
                {
                    # Input
                    "straatnaam": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "bag_huisletter": "A",
                    "bag_toevoeging": "I",
                },
                {
                    # Expected output
                    "openbare_ruimte": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "huisletter": "A",
                    "huisnummer_toevoeging": "I"
                }
            ),
            (
                {
                    # Input
                    "straatnaam": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "bag_huisletter": "",
                    "bag_toevoeging": "",
                },
                {
                    # Expected output
                    "openbare_ruimte": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "huisletter": "",
                    "huisnummer_toevoeging": ""
                }
            )
        ]

        for input_data, expected_result in test_cases:
            result = address_validation._atlas_result_to_address(input_data)

            self.assertEquals(expected_result, result)
