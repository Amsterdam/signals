# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from json import dumps, load
from os.path import abspath, dirname, join
from unittest.mock import MagicMock

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase
from requests.exceptions import ConnectionError
from requests_mock.mocker import Mocker
from rest_framework.exceptions import ValidationError

from signals.apps.api.validation.address.base import (
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.api.validation.address.mixin import AddressValidationMixin
from signals.apps.api.validation.address.pdok import PDOKAddressValidation


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

    def test_no_results_allow_unverified(self):
        address_validation = PDOKAddressValidation()
        address_validation._search = MagicMock(return_value=[])

        validation_mixin = AddressValidationMixin()
        validation_mixin.get_address_validation = MagicMock(return_value=address_validation)

        location_data = {
            'geometrie': Point(4.898466, 52.361585),
            'address': self.address_dict,
        }

        with self.settings(ALLOW_INVALID_ADDRESS_AS_UNVERIFIED=False):
            self.assertRaises(ValidationError, validation_mixin.validate_location, location_data)
        with self.settings(ALLOW_INVALID_ADDRESS_AS_UNVERIFIED=True):
            try:
                validation_mixin.validate_location(location_data)
            except ValidationError:
                self.fail("Should not raise exception because of setting")

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
