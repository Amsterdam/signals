import copy

from django.test import TransactionTestCase

from signals.apps.signals.utils.location import AddressFormatter


class TestAddressFormatter(TransactionTestCase):
    def setUp(self):
        self.address = {
            'openbare_ruimte': 'Amstel',
            'huisnummer': 1,
            'huisletter': '',
            'huisnummer_toevoeging': '',
            'postcode': '1011PN',
            'woonplaats': 'Amsterdam'
        }

    def test_format(self):
        address_formatter = AddressFormatter(address=self.address)

        formatted_address_str = address_formatter.format(format_str='O hlT, P W')
        self.assertEqual(formatted_address_str, 'Amstel 1, 1011 PN Amsterdam')

    def test_single_formats(self):
        address_formatter = AddressFormatter(address=self.address)

        formatted_address_str = address_formatter.format(format_str='O')
        self.assertEqual(formatted_address_str, 'Amstel')

        formatted_address_str = address_formatter.format(format_str='h')
        self.assertEqual(formatted_address_str, '1')

        formatted_address_str = address_formatter.format(format_str='l')
        self.assertEqual(formatted_address_str, '')

        formatted_address_str = address_formatter.format(format_str='t')
        self.assertEqual(formatted_address_str, '')

        formatted_address_str = address_formatter.format(format_str='T')
        self.assertEqual(formatted_address_str, '')

        formatted_address_str = address_formatter.format(format_str='p')
        self.assertEqual(formatted_address_str, '1011PN')

        formatted_address_str = address_formatter.format(format_str='P')
        self.assertEqual(formatted_address_str, '1011 PN')

        formatted_address_str = address_formatter.format(format_str='W')
        self.assertEqual(formatted_address_str, 'Amsterdam')

    def test_single_formats_with_huisletter_and_huisnummer_toevoeging(self):
        address = copy.deepcopy(self.address)
        address['huisletter'] = 'X'
        address['huisnummer_toevoeging'] = 'Y'

        address_formatter = AddressFormatter(address=address)

        formatted_address_str = address_formatter.format(format_str='O')
        self.assertEqual(formatted_address_str, 'Amstel')

        formatted_address_str = address_formatter.format(format_str='h')
        self.assertEqual(formatted_address_str, '1')

        formatted_address_str = address_formatter.format(format_str='l')
        self.assertEqual(formatted_address_str, 'X')

        formatted_address_str = address_formatter.format(format_str='t')
        self.assertEqual(formatted_address_str, 'Y')

        formatted_address_str = address_formatter.format(format_str='T')
        self.assertEqual(formatted_address_str, '-Y')

        formatted_address_str = address_formatter.format(format_str='p')
        self.assertEqual(formatted_address_str, '1011PN')

        formatted_address_str = address_formatter.format(format_str='P')
        self.assertEqual(formatted_address_str, '1011 PN')

        formatted_address_str = address_formatter.format(format_str='W')
        self.assertEqual(formatted_address_str, 'Amsterdam')

    def test_non_existing_formats(self):
        address_formatter = AddressFormatter(address=self.address)

        formatted_address_str = address_formatter.format(format_str='x')
        self.assertEqual(formatted_address_str, 'x')

        formatted_address_str = address_formatter.format(format_str='X')
        self.assertEqual(formatted_address_str, 'X')

        formatted_address_str = address_formatter.format(format_str='y')
        self.assertEqual(formatted_address_str, 'y')

        formatted_address_str = address_formatter.format(format_str='Y')
        self.assertEqual(formatted_address_str, 'Y')

        formatted_address_str = address_formatter.format(format_str='z')
        self.assertEqual(formatted_address_str, 'z')

        formatted_address_str = address_formatter.format(format_str='Z')
        self.assertEqual(formatted_address_str, 'Z')

    def test_address_none_type(self):
        address_formatter = AddressFormatter(address=None)
        formatted_address_str = address_formatter.format(format_str='O')
        self.assertEqual(formatted_address_str, '')
