"""
Tests the full flow that Techtek uses.

Note that this tests the initial version of the relevant flow, future per
category permissions will complicate the flow somewhat.
"""
# TODO:
# - correct / incorrect address
# - ...

import copy

from django.contrib.auth.models import Permission
from django.utils.http import urlencode

from signals.apps.signals import workflow
from signals.apps.signals.models import Category
from tests.apps.signals.factories import SignalFactory, SignalFactoryValidLocation
from tests.apps.users.factories import UserFactory
from tests.test import SignalsBaseApiTestCase

NEW_SIGNAL = {
    'source': 'TechView',
    'text': 'kapotte lantaarn',
    'text_extra': 'Omschrijving?',
    'location': {
        'geometrie': {
            'type': 'Point',
            'coordinates': [
                4.982279608954491,
                52.321013255241425,
            ],
        },
        'stadsdeel': 'A',
        'buurt_code': 'A04i',
    },
    'category': {
        'sub_category': 'http://testserver/category/ur/replace/in/tests',
    },
    'reporter': {
        'email': 'someone@techtek.nl',
        'phone': '0000000000',
    },
    'incident_date_start': '2019-02-26T00:00:00+0100',
}
PATCH_SIGNAL_STATUS = {
    'status': {
        'state': 'REPLACE WITH CORRECT STATE STRING',
        'text': 'REPLACE WITH RELEVANT STATUS MESSAGE',
    }
}
TECHTEK_MAIN_SLUG = 'wegen-verkeer-straatmeubilair'
TECHTEK_SUB_SLUG = 'straatverlichting-openbare-klok'

NOT_TECHTEK_MAIN_SLUG = 'afval'
NOT_TECHTEK_SUB_SLUG = 'asbest-accu'


class TestTechtekFlow(SignalsBaseApiTestCase):
    fixtures = ['categories.json', ]

    def setUp(self):
        """Setup test environment"""
        # Create a test user for Techtek.
        self.techtek_user = UserFactory(
            email='someone@techtek.nl'
        )
        # Give the Techtek user the correct permissions.
        required_permissions = Permission.objects.filter(codename__in=['sia_read', 'sia_write'])
        self.techtek_user.user_permissions.set(required_permissions)

        # Various relevant endpoints
        self.signals_list = '/signals/v1/private/signals/'
        self.signal_detail = '/signals/v1/private/signals/{pk}'
        self.category_url_template = \
            '{server}/signals/v1/public/terms/categories/{main_slug}/sub_categories/{sub_slug}'

        # Fill test database with some signals to demonstrate filtering.
        techtek_sub_cat = Category.objects.get(
            parent__slug=TECHTEK_MAIN_SLUG,
            slug=TECHTEK_SUB_SLUG,
        )

        self._techtek_signal_1 = SignalFactoryValidLocation(
            category_assignment__category=techtek_sub_cat,
            text='De straatverlichting werkt niet.',
            status__state=workflow.GEMELD,
        )
        self._techtek_signal_2 = SignalFactoryValidLocation(
            category_assignment__category=techtek_sub_cat,
            text='De openbare klok op de hoek werkt niet.',
            status__state=workflow.AFGEHANDELD,
        )

        other_cat = Category.objects.get(
            parent__slug=NOT_TECHTEK_MAIN_SLUG,
            slug=NOT_TECHTEK_SUB_SLUG,
        )
        self._signal = SignalFactory(
            category_assignment__category=other_cat,
            text='Er ligt een accu in de sloot.',
            status__state=workflow.GEMELD,
        )

    def test_create_new_signal_via_api(self):
        """Create a new signal via API, example."""
        # We are using the private API which requires authenticated requests
        self.client.force_authenticate(user=self.techtek_user)

        # Create a body for the POST that creates a new signal (via private API)
        post_data = copy.deepcopy(NEW_SIGNAL)
        post_data['category']['sub_category'] = self.category_url_template.format(**{
            'server': 'http://testserver',  # Should be set to correct server in real world.
            'main_slug': TECHTEK_MAIN_SLUG,
            'sub_slug': TECHTEK_SUB_SLUG,
        })

        response = self.client.post(
            '/signals/v1/private/signals/',
            post_data,
            format='json'
        )

        # Check that a new signal was actually created with correct properties.
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['category']['main_slug'], TECHTEK_MAIN_SLUG)
        self.assertEqual(data['category']['sub_slug'], TECHTEK_SUB_SLUG)

    def test_request_signals_in_techtek_category_and_handle_them(self):
        """Retrieve signals in Techteks category and handle one of them."""
        # We are using the private API which requires authenticated requests
        self.client.force_authenticate(user=self.techtek_user)

        # Request a list of signals in Techteks category, filtering is done
        # using URL query parameters 'maincategory_slug' and 'category_slug'.
        querystring = urlencode({
            'maincategory_slug': TECHTEK_MAIN_SLUG,
            'category_slug': TECHTEK_SUB_SLUG,
            'status': workflow.GEMELD,
        })
        response = self.client.get(self.signals_list + '?' + querystring)
        self.assertEqual(response.status_code, 200)

        # We should find only one matching signal in Techteks category with
        # status GEMELD.
        list_data = response.json()
        self.assertEqual(list_data['count'], 1)
        signal_data = list_data['results'][0]  # There might be more signals, in this test only one.
        self.assertEqual(signal_data['status']['state'], workflow.GEMELD)
        signal_id = signal_data['id']

        # Create message body for status updates
        status_update_msg = 'Techtek heeft deze melding in behandeling genomen.'
        patch_json = copy.deepcopy(PATCH_SIGNAL_STATUS)
        patch_json['status']['state'] = workflow.BEHANDELING
        patch_json['status']['text'] = status_update_msg

        # Still authenticated as Techtek user!
        response = self.client.patch(
            self.signal_detail.format(**{'pk': signal_id}),
            patch_json,
            format='json'
        )

        # Successfull PATCH produces HTTP 200
        self.assertEqual(response.status_code, 200)

        # Another update
        status_update_msg = 'Er is een monteur langsgeweest.'
        patch_json = copy.deepcopy(PATCH_SIGNAL_STATUS)
        patch_json['status']['state'] = workflow.BEHANDELING
        patch_json['status']['text'] = status_update_msg

        response = self.client.patch(
            self.signal_detail.format(**{'pk': signal_id}),
            patch_json,
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        # We are done, close the Signal.
        # NOTE: this will change when new special status is added to SIA to
        # signal that an external party is ready and SIA backoffice worker
        # should close the Signal (so that the reporter gets mailed).
        status_update_msg = 'De lantaarn is gerepareerd.'
        patch_json = copy.deepcopy(PATCH_SIGNAL_STATUS)
        patch_json['status']['state'] = workflow.AFGEHANDELD
        patch_json['status']['text'] = status_update_msg

        response = self.client.patch(
            self.signal_detail.format(**{'pk': signal_id}),
            patch_json,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
