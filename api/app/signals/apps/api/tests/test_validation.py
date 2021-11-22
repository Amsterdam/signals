# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import json
import os
from unittest.mock import patch

from django.test import TestCase

from signals.apps.api.validation.address.pdok import PDOKAddressValidation

THIS_DIR = os.path.dirname(__file__)
# These JSON files were created from PDOK locatieserver V3 responses. Both
# municipalities contain an street and housenumber Achtergracht 72.
JSON_AMSTERDAM = 'pdok_response_amsterdam.json'
JSON_WEESP = 'pdok_response_weesp.json'

IN_AMSTERDAM = (4.898466, 52.361585)
IN_WEESP = (5.042758, 52.306766)


class TestPDOKValidation(TestCase):
    def _load_response_json(self, filename):
        with open(os.path.join(THIS_DIR, 'response_json', filename), 'r') as f:
            return json.load(f)

    @patch('signals.apps.api.validation.address.pdok.PDOKAddressValidation._search', autospec=True)
    def test_in_amsterdam_validation(self, patched_search):
        pdok_response = self._load_response_json(JSON_AMSTERDAM)
        patched_search.return_value = pdok_response['response']['docs']

        address = {'openbare_ruimte': 'Achtergracht', 'huisnummer': 72}
        lon, lat = IN_AMSTERDAM
        validation = PDOKAddressValidation()
        validated_address = validation.validate_address(address=address, lon=lon, lat=lat)

        self.assertEqual(validated_address['openbare_ruimte'], 'Nieuwe Achtergracht')
        self.assertEqual(validated_address['postcode'], '1018XZ')
        self.assertEqual(validated_address['huisnummer'], 72)
        self.assertEqual(validated_address['woonplaats'], 'Amsterdam')

    @patch('signals.apps.api.validation.address.pdok.PDOKAddressValidation._search', autospec=True)
    def test_in_weesp_validation(self, patched_search):
        pdok_response = self._load_response_json(JSON_WEESP)
        patched_search.return_value = pdok_response['response']['docs']

        address = {'openbare_ruimte': 'Achtergracht', 'huisnummer': 72}
        lon, lat = IN_WEESP
        validation = PDOKAddressValidation()
        validated_address = validation.validate_address(address=address, lon=lon, lat=lat)

        self.assertEqual(validated_address['openbare_ruimte'], 'Achtergracht')
        self.assertEqual(validated_address['postcode'], '1381BP')
        self.assertEqual(validated_address['huisnummer'], 72)
        self.assertEqual(validated_address['woonplaats'], 'Weesp')
