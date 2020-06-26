from django.test import TestCase

from signals.apps.api.v1.validation.address.pdok import PDOKAddressValidation

IN_AMSTERDAM = (4.898466, 52.361585)
IN_WEESP = (5.042758, 52.306766)


class TestPDOKValidation(TestCase):
    def test_in_amsterdam_validation(self):
        address = {'openbare_ruimte': 'Achtergracht', 'huisnummer': 72}
        lon, lat = IN_AMSTERDAM
        validation = PDOKAddressValidation()
        validated_address = validation.validate_address(address=address, lon=lon, lat=lat)

        self.assertEqual(validated_address['openbare_ruimte'], 'Nieuwe Achtergracht')
        self.assertEqual(validated_address['postcode'], '1018XZ')
        self.assertEqual(validated_address['huisnummer'], 72)
        self.assertEqual(validated_address['woonplaats'], 'Amsterdam')

    def test_in_weesp_validation(self):
        address = {'openbare_ruimte': 'Achtergracht', 'huisnummer': 72}
        lon, lat = IN_WEESP
        validation = PDOKAddressValidation()
        validated_address = validation.validate_address(address=address, lon=lon, lat=lat)

        self.assertEqual(validated_address['openbare_ruimte'], 'Achtergracht')
        self.assertEqual(validated_address['postcode'], '1381BP')
        self.assertEqual(validated_address['huisnummer'], 72)
        self.assertEqual(validated_address['woonplaats'], 'Weesp')
