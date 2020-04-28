from json import dumps, load
from os.path import abspath, dirname, join
from unittest.mock import MagicMock

from django.conf import settings
from django.test import SimpleTestCase
from requests.exceptions import ConnectionError
from requests_mock.mocker import Mocker

from signals.apps.api.v1.validation.address.bag import AddressValidation
from signals.apps.api.v1.validation.address.base import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.api.v1.validation.address.pdok import PDOKAddressValidation


class TestPDOKAddressValidation(SimpleTestCase):
    PDOK_RESPONSE_JSON = "pdok_result.json"
    pdok_response = None
    address_dict = {
        "openbare_ruimte": "Geuzenkade",
        "huisnummer": 55,
        "huisletter": "",
        "huisnummer_toevoeging": "1",
        "postcode": "1056KN",
        "woonplaats": "Amsterdam"
    }

    def _get_mocked_response(self):
        if self.pdok_response is None:
            with open(join(dirname(abspath(__file__)), self.PDOK_RESPONSE_JSON)) as f:
                self.pdok_response = load(f)
        return self.pdok_response

    def test_no_results(self):
        address_validation = PDOKAddressValidation()
        address_validation._search = MagicMock(return_value=[])

        self.assertRaises(NoResultsException, address_validation.validate_address, self.address_dict)

        address_validation._search.assert_called_with(self.address_dict)

    def test_address_found(self):
        address_validation = PDOKAddressValidation()

        result = self._get_mocked_response()["response"]["docs"][0]

        address_validation._search = MagicMock(return_value=[result])
        address_validation._search_result_to_address = MagicMock()

        address_validation.validate_address(self.address_dict)

        address_validation._search.assert_called_with(self.address_dict)
        address_validation._search_result_to_address.assert_called_with(result)

    def test_search_unavailable(self):
        address_validation = PDOKAddressValidation()

        with Mocker() as m:
            m.get(address_validation.address_validation_url, status_code=400)
            self.assertRaises(AddressValidationUnavailableException, address_validation._search, self.address_dict)

    def test_search_connection_error(self):
        address_validation = PDOKAddressValidation()

        with Mocker() as m:
            m.get(address_validation.address_validation_url, exc=ConnectionError)
            self.assertRaises(AddressValidationUnavailableException, address_validation._search, self.address_dict)

    def test_search_successful_request(self):
        address_validation = PDOKAddressValidation()

        result = self._get_mocked_response()
        expected = result["response"]["docs"]

        with Mocker() as m:
            m.get(address_validation.address_validation_url, text=dumps(result))
            self.assertEqual(address_validation._search(self.address_dict), expected)


class TestBAGAddressValidation(SimpleTestCase):
    ATLAS_RESPONSE_JSON = "atlas_result.json"
    atlas_response = None
    address = "Weesperstraat 113"
    address_dict = {
        "openbare_ruimte": "Weesperstraat",
        "huisnummer": 113,
    }

    def _get_file_path(self, relative_file):
        return join(dirname(abspath(__file__)), relative_file)

    def _get_atlas_response(self):
        if self.atlas_response is None:
            with open(self._get_file_path(self.ATLAS_RESPONSE_JSON)) as f:
                self.atlas_response = load(f)

        return self.atlas_response

    def _get_atlas_search_url(self):
        return settings.DATAPUNT_API_URL + 'atlas/search/adres'

    def test_validate_address_string_no_results(self):
        address_validation = AddressValidation()

        address_validation._search = MagicMock(return_value=[])

        self.assertRaises(NoResultsException, address_validation.validate_address, self.address_dict)

        address_validation._search.assert_called_with(self.address_dict)

    def test_validate_address_string_with_results(self):
        address_validation = AddressValidation()

        atlas_first_result = self._get_atlas_response()["results"][0]

        address_validation._search = MagicMock(return_value=[atlas_first_result])
        address_validation._search_result_to_address = MagicMock()

        address_validation.validate_address(self.address_dict)

        address_validation._search.assert_called_with(self.address_dict)
        address_validation._search_result_to_address.assert_called_with(atlas_first_result)

    def test_address_dict_to_string(self):
        address_validation = AddressValidation()

        test_cases = [
            (
                {
                    "openbare_ruimte": "Weesperstraat",
                    "huisnummer": 113,
                },
                "Weesperstraat 113",
            ),
            (
                {
                    "openbare_ruimte": "Weesperstraat",
                    "huisnummer": 113,
                    "huisletter": "A",
                },
                "Weesperstraat 113A",
            ),
            (
                {
                    "openbare_ruimte": "Weesperstraat",
                    "huisnummer": 113,
                    "huisletter": "A",
                    "huisnummer_toevoeging": "1",
                },
                "Weesperstraat 113A-1",
            ),
            (
                {
                    "openbare_ruimte": "Weesperstraat",
                    "huisnummer": 113,
                    "huisnummer_toevoeging": "1",
                },
                "Weesperstraat 113-1",
            ),
        ]

        for test_case in test_cases:
            self.assertEqual(test_case[1], address_validation._address_dict_to_string(test_case[0]))

    def test_search_atlas_with_unsuccessful_http_code(self):
        address_validation = AddressValidation()

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), status_code=400)
            self.assertRaises(AddressValidationUnavailableException, address_validation._search, self.address_dict)

    def test_search_atlas_with_connection_error(self):
        address_validation = AddressValidation()

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), exc=ConnectionError)
            self.assertRaises(AddressValidationUnavailableException, address_validation._search, self.address_dict)

    def test_search_atlas_successful_request(self):
        address_validation = AddressValidation()

        search_result = self._get_atlas_response()
        expected = search_result["results"]

        with Mocker() as m:
            m.get(self._get_atlas_search_url(), text=dumps(search_result))
            self.assertEqual(address_validation._search(self.address_dict), expected)

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
                    "woonplaats": "Amsterdam",
                },
                {
                    # Expected output
                    "openbare_ruimte": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "huisletter": "A",
                    "huisnummer_toevoeging": "I",
                    "woonplaats": "Amsterdam",
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
                    "woonplaats": "Amsterdam",
                },
                {
                    # Expected output
                    "openbare_ruimte": "Weesperstraat",
                    "postcode": "1018VN",
                    "huisnummer": 113,
                    "huisletter": "",
                    "huisnummer_toevoeging": "",
                    "woonplaats": "Amsterdam",
                }
            )
        ]

        for input_data, expected_result in test_cases:
            result = address_validation._search_result_to_address(input_data)
            self.assertEqual(expected_result, result)
