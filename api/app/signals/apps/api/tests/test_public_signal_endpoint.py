# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import copy
import json
import os
from datetime import timedelta
from unittest import skip
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.api.serializers.attachment import PUBLIC_UPLOAD_ALLOWED_STATES
from signals.apps.api.validation.address.base import AddressValidationUnavailableException
from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.models import Feedback
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryFactory,
    ParentCategoryFactory,
    SignalFactory,
    SourceFactory
)
from signals.apps.signals.models import Attachment, Priority, Signal, Type
from signals.apps.signals.tests.attachment_helpers import small_gif
from signals.apps.signals.workflow import AFGEHANDELD, GEMELD, STATUS_CHOICES
from signals.test.utils import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPublicSignalViewSet(SignalsBaseApiTestCase):
    list_endpoint = "/signals/v1/public/signals/"
    detail_endpoint = list_endpoint + "{uuid}"
    attachment_endpoint = detail_endpoint + "/attachments"

    fixture_file = os.path.join(THIS_DIR, 'request_data', 'create_initial_public.json')

    def setUp(self):
        with open(self.fixture_file, 'r') as f:
            self.create_initial_data = json.load(f)

        self.subcategory = CategoryFactory.create()

        self.link_test_cat_sub = '/signals/v1/public/terms/categories/{}/sub_categories/{}'.format(
            self.subcategory.parent.slug, self.subcategory.slug
        )

        self.create_initial_data['category'] = {'sub_category': self.link_test_cat_sub}

        self.retrieve_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'get_signals_v1_public_signals_{uuid}.json'
            )
        )
        self.create_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_public_signals.json'
            )
        )
        self.create_attachment_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_public_signals_attachment.json'
            )
        )

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_nothing_special(self, validate_address):
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_schema, response.json())
        self.assertEqual(1, Signal.objects.count())

        signal = Signal.objects.last()
        self.assertEqual(workflow.GEMELD, signal.status.state)
        self.assertEqual(self.subcategory, signal.category_assignment.category)
        self.assertEqual("melder@example.com", signal.reporter.email)
        self.assertEqual("Amstel 1 1011PN Amsterdam", signal.location.address_text)
        self.assertEqual("Luidruchtige vergadering", signal.text)
        self.assertEqual("extra: heel luidruchtig debat", signal.text_extra)
        self.assertEqual('SIG', signal.type_assignment.name)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_status(self, validate_address):
        """ Tests that an error is returned when we try to set the status """

        self.create_initial_data["status"] = {
            "state": workflow.BEHANDELING,
            "text": "Invalid stuff happening here"
        }

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_priority(self, validate_address):
        # must not be able to set priority
        self.create_initial_data['priorty'] = {
            'priority': Priority.PRIORITY_HIGH
        }
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_type(self, validate_address):
        # must not be able to set type
        self.create_initial_data['type'] = {
            'code': Type.COMPLAINT
        }
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_extra_properties_missing(self, validate_address):
        # "extra_properties" missing <- must be accepted
        del self.create_initial_data['extra_properties']
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_extra_properties_null(self, validate_address):
        # "extra_properties": null <- must be accepted
        self.create_initial_data['extra_properties'] = None
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_extra_properties_empty_object(self, validate_address):
        # "extra_properties": {} <- must not be accepted
        self.create_initial_data['extra_properties'] = {}
        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

    def test_get_by_uuid(self):
        signal = SignalFactory.create()

        response = self.client.get(self.detail_endpoint.format(uuid=signal.uuid), format='json')

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response.json())

    def test_get_by_uuid_does_not_exists(self):
        response = self.client.get(self.detail_endpoint.format(uuid='00000000-0000-0000-0000-000000000000'),
                                   format='json')
        self.assertEqual(404, response.status_code)

    def test_get_by_uuid_access_status(self):
        # SIA must not publicly expose what step in the resolution process a certain
        # Signal/melding is
        signal = SignalFactory.create(status__state=workflow.GEMELD)

        response = self.client.get(self.detail_endpoint.format(uuid=signal.uuid), format='json')
        response_json = response.json()

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response_json)
        self.assertEqual(response_json['status']['state'], 'OPEN')

        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)

        response = self.client.get(self.detail_endpoint.format(uuid=signal.uuid), format='json')
        response_json = response.json()

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response_json)
        self.assertEqual(response_json['status']['state'], 'CLOSED')

    def test_get_by_uuid__display_is_clean(self):
        # SIA must not publicly expose what step in the resolution process a certain
        # Signal/melding is via the _display string.
        signal = SignalFactory.create()

        response = self.client.get(self.detail_endpoint.format(uuid=signal.uuid), format='json')
        response_json = response.json()

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response_json)
        # For backwards compatibility the _display string is not changed, we use the
        # fact that it is derived from the __str__ representation, to do this check.
        self.assertNotEqual(response_json['_display'], str(signal))

    def test_get_by_uuid_cannot_access_properties(self):
        # SIA must not publicly expose operational date, expire_date and attachments
        signal = SignalFactory.create()

        response = self.client.get(self.detail_endpoint.format(uuid=signal.uuid), format='json')
        response_json = response.json()

        self.assertEqual(200, response.status_code)
        self.assertJsonSchema(self.retrieve_schema, response_json)
        self.assertNotIn('operational_date', response_json)
        self.assertNotIn('expire_date', response_json)
        self.assertNotIn('attachments', response_json)

    def test_add_attachment_imagetype(self):
        signal = SignalFactory.create(status__state=GEMELD)

        data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}

        response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_attachment_schema, response.json())

        attachment = Attachment.objects.last()
        self.assertEqual("image/gif", attachment.mimetype)
        self.assertIsNone(attachment.created_by)

    def test_add_attachment_extension_not_allowed(self):
        signal = SignalFactory.create(status__state=GEMELD)

        doc_upload = os.path.join(THIS_DIR, 'test-data', 'sia-ontwerp-testfile.doc')
        with open(doc_upload, encoding='latin-1') as f:
            data = {"file": f}

            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)

        self.assertEqual(response.status_code, 400)

    def test_add_attachment_in_correct_state_allowed(self):
        # Uploads should be allowed when a reaction is requested or when the signal is newly created.
        signal = SignalFactory.create(status__state=GEMELD)

        # AFGEHANDELD has extra rules, we do not test them here. See test_add_attachment_in_state_AFGEHANDELD.
        allowed_states = set(PUBLIC_UPLOAD_ALLOWED_STATES)
        allowed_states.remove(AFGEHANDELD)

        for state in allowed_states:
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            signal.status.state = state
            signal.status.save()

            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 201)

    @patch('signals.apps.api.serializers.attachment.PUBLIC_UPLOAD_ALLOWED_STATES', new=(AFGEHANDELD,))
    def test_add_attachment_in_state_AFGEHANDELD(self):
        # When a nuisance complaint is handled it transitions to the state
        # AFGEHANDELD and a feedback request is potentially sent. If such a
        # feedback request is open, images can be part of that feedback.
        self.assertLess(0, FEEDBACK_EXPECTED_WITHIN_N_DAYS)
        attachment_count = Attachment.objects.count()
        now = timezone.now()

        with freeze_time(now):
            signal = SignalFactory.create(status__state=GEMELD)
            signal.status.state = AFGEHANDELD
            signal.status.save()

        # No feedback requested => no uploads allowed.
        with freeze_time(now + timedelta(seconds=3600)):
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('No feedback expected for this signal hence no uploads allowed.', response.json())
            self.assertEqual(Attachment.objects.count(), attachment_count)

        # Feedback requested and request still open => uploads allowed.
        with freeze_time(now + timedelta(seconds=3600)):
            feedback = Feedback.actions.request_feedback(signal)
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Attachment.objects.count(), attachment_count + 1)

        # Feedback requested and feedback too late => no uploads allowed.
        with freeze_time(now + timedelta(days=2 * FEEDBACK_EXPECTED_WITHIN_N_DAYS)):
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('No feedback expected for this signal hence no uploads allowed.', response.json())
            self.assertEqual(Attachment.objects.count(), attachment_count + 1)

        # Feedback requested and feedback already filled out => no uploads allowed.
        with freeze_time(now + timedelta(seconds=7200)):
            feedback.submitted_at = now + timedelta(seconds=7200)
            feedback.save()

            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('No feedback expected for this signal hence no uploads allowed.', response.json())
            self.assertEqual(Attachment.objects.count(), attachment_count + 1)

    @patch('signals.apps.api.serializers.attachment.PUBLIC_UPLOAD_ALLOWED_STATES', new=(AFGEHANDELD,))
    def test_add_attachment_in_state_AFGEHANDELD_several_feedback_requests(self):
        # Several feedback requests can be open at once. In this test we open
        # two feedback requests and provide feedback to the second one. The
        # first one will still be open and we check that we can still upload
        # attachments.
        self.assertLess(0, FEEDBACK_EXPECTED_WITHIN_N_DAYS)
        attachment_count = Attachment.objects.count()
        now = timezone.now()

        with freeze_time(now):
            signal = SignalFactory.create(status__state=GEMELD)
            signal.status.state = AFGEHANDELD
            signal.status.save()

        with freeze_time(now + timedelta(seconds=1800)):
            # First feedback object that we leave open.
            Feedback.actions.request_feedback(signal)

        with freeze_time(now + timedelta(seconds=3600)):
            # Second feedback object (closed state)
            feedback2 = Feedback.actions.request_feedback(signal)
            feedback2.submitted_at = now + timedelta(seconds=7200)
            feedback2.save()

        with freeze_time(now + timedelta(seconds=7200)):
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Attachment.objects.count(), attachment_count + 1)

    def test_add_attachment_in_wrong_state_not_allowed(self):
        # We don't want people to upload images long after creating the original
        # nuisance complaint was created.
        signal = SignalFactory.create(status__state=GEMELD)
        not_allowed = set(x[0] for x in STATUS_CHOICES) - set(PUBLIC_UPLOAD_ALLOWED_STATES)

        for state in not_allowed:
            data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}
            signal.status.state = state
            signal.status.save()

            response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)
            self.assertEqual(response.status_code, 400)
            self.assertIn('Public uploads not allowed in current signal state.', response.json())

    def test_cannot_access_attachments(self):
        # SIA must not publicly expose attachments
        signal = SignalFactory.create()

        response = self.client.get(self.attachment_endpoint.format(uuid=signal.uuid))
        self.assertEqual(response.status_code, 405)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_validate_extra_properties_enabled(self, validate_address):
        self.create_initial_data['extra_properties'] = [{
            'id': 'test_id',
            'label': 'test_label',
            'answer': {
                'id': 'test_answer',
                'value': 'test_value'
            },
            'category_url': self.link_test_cat_sub
        }, {
            'id': 'test_id',
            'label': 'test_label',
            'answer': 'test_answer',
            'category_url': self.link_test_cat_sub
        }, {
            'id': 'test_id',
            'label': 'test_label',
            'answer': ['a', 'b', 'c'],
            'category_url': self.link_test_cat_sub
        }]

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_validate_extra_properties_enabled_invalid_data(self, validate_address):
        self.create_initial_data['extra_properties'] = {'old_style': 'extra_properties'}

        response = self.client.post(self.list_endpoint, self.create_initial_data, format='json')
        data = response.json()

        self.assertEqual(400, response.status_code)
        self.assertIn('extra_properties', data)
        self.assertEqual(data['extra_properties'][0], 'Invalid input.')
        self.assertEqual(0, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_validate_extra_properties_enabled_invalid_category_url(self, validate_address):
        create_initial_data = copy.deepcopy(self.create_initial_data)

        create_initial_data['extra_properties'] = [{'id': 'test_id', 'label': 'test_label', 'answer': 'test',
                                                    'category_url': 'invalid value'}]

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')
        data = response.json()

        self.assertEqual(400, response.status_code)
        self.assertIn('extra_properties', data)
        self.assertEqual(data['extra_properties'][0], 'Invalid input.')
        self.assertEqual(0, Signal.objects.count())

        create_initial_data['extra_properties'] = [{'id': 'test_id', 'label': 'test_label', 'answer': 'test',
                                                    'category_url': ''}]

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')
        data = response.json()

        self.assertEqual(400, response.status_code)
        self.assertIn('extra_properties', data)
        self.assertEqual(data['extra_properties'][0], 'Invalid input.')
        self.assertEqual(0, Signal.objects.count())

    def test_get_list(self):
        response = self.client.get(f'{self.list_endpoint}')
        self.assertEqual(response.status_code, 404)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_interne_melding(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = copy.deepcopy(self.create_initial_data)
        initial_data['reporter']['email'] = 'test-email-1' \
                                            f'{settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS}'
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        data = response.json()
        signal = Signal.objects.get(pk=data['id'])
        self.assertEqual(signal.source, settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE)

        initial_data = copy.deepcopy(self.create_initial_data)
        # Added a trailing space to the email, this should be removed
        initial_data['reporter']['email'] = 'trailing-space-should-be-removed' \
                                            f'{settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS} '
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 2)

        data = response.json()
        signal = Signal.objects.get(pk=data['id'])
        self.assertEqual(signal.source, settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE)

    @override_settings(API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS=('uitzondering@amsterdam.nl',))
    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_initial_signal_interne_melding_check_exceptions(self, validate_address):
        signal_count = Signal.objects.count()

        initial_data = copy.deepcopy(self.create_initial_data)
        initial_data['reporter']['email'] = 'uitzondering@amsterdam.nl'
        response = self.client.post(self.list_endpoint, initial_data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Signal.objects.count(), signal_count + 1)

        data = response.json()
        signal = Signal.objects.get(pk=data['id'])
        self.assertEqual(signal.source, 'online')  # online is model default and is used for non-logged in users

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_source_online(self, validate_address):
        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data.update({'source': 'online'})
        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_schema, response.json())
        self.assertEqual(1, Signal.objects.count())

        signal = Signal.objects.last()
        self.assertEqual(signal.source, 'online')

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_source_with_is_public_property_set_to_true(self, validate_address):
        public_source = SourceFactory.create(is_public=True)

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data.update({'source': public_source.name})
        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_schema, response.json())
        self.assertEqual(1, Signal.objects.count())

        signal = Signal.objects.last()
        self.assertEqual(signal.source, public_source.name)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_source_with_is_public_property_set_to_false(self, validate_address):
        private_source = SourceFactory.create(is_public=False)

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data.update({'source': private_source.name})
        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, Signal.objects.count())

        response_json = response.json()
        self.assertEqual(len(response_json['source']), 1)
        self.assertEqual(response_json['source'][0], 'Invalid source given, value not known')

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_session(self, validate_address):
        create_initial_data = copy.deepcopy(self.create_initial_data)

        session = SessionFactory.create(submit_before=timezone.now() + timezone.timedelta(hours=2), frozen=True)
        create_initial_data.update({'session': session.uuid})

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_schema, response.json())
        self.assertEqual(1, Signal.objects.count())

        session.refresh_from_db()
        signal = Signal.objects.first()
        self.assertEqual(session._signal_id, signal.id)

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_not_frozen_session(self, validate_address):
        signal_count = Signal.objects.count()
        create_initial_data = copy.deepcopy(self.create_initial_data)

        session = SessionFactory.create(submit_before=timezone.now() + timezone.timedelta(hours=2))
        create_initial_data.update({'session': session.uuid})

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json()['session'][0], 'Session not frozen')
        self.assertEqual(signal_count, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_expired_session(self, validate_address):
        create_initial_data = copy.deepcopy(self.create_initial_data)

        session = SessionFactory.create(submit_before=timezone.now() - timezone.timedelta(hours=2))
        create_initial_data.update({'session': session.uuid})

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json()['session'][0], 'Session expired')
        self.assertEqual(0, Signal.objects.count())

    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_with_session_connected_to_another_signal(self, validate_address):
        another_signal = SignalFactory.create()
        session = SessionFactory.create(_signal=another_signal, frozen=False,
                                        submit_before=timezone.now() + timezone.timedelta(hours=2))

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data.update({'session': session.uuid})

        response = self.client.post(self.list_endpoint, create_initial_data, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json()['session'][0], 'Session already used')
        self.assertEqual(1, Signal.objects.count())

        session.refresh_from_db()
        self.assertEqual(session._signal_id, another_signal.id)

    @skip('Disbaled the check on the extra propeties, this causes an issue when creating "child" signals')
    @patch('signals.apps.api.validation.address.base.BaseAddressValidation.validate_address',
           side_effect=AddressValidationUnavailableException)  # Skip address validation
    def test_create_and_validate_extra_properties_for_streetlights(self, validate_address):
        """
        Disabled the additional check. This check prevents the creation of a "child" signal in the
        lantaarnpaal-straatverlichting category because there is no way to provide the streetlight

        SIG-4382 [BE] Extra check op formaat en inhoud van extra_properties bij de verlichting sub categorien
        (tbv koppeling Techview)

        To make sure we accept the valid data in the extra properties when a Signal is created for the category
        containing streetlights we are adding an additional check.
        """
        parent_category = ParentCategoryFactory.create(slug='wegen-verkeer-straatmeubilair')
        link_main_category = f'/signals/v1/public/terms/categories/{parent_category.slug}'

        child_category = CategoryFactory.create(slug='lantaarnpaal-straatverlichting', parent=parent_category)
        link_sub_category = f'{link_main_category}/sub_categories/{child_category.slug}'

        extra_properties_none = None
        extra_properties_empty_list = []
        extra_properties_not_on_map_simple = [
            {
                'id': 'extra_straatverlichting_nummer',
                'label': 'Lichtpunt(en) op kaart',
                'category_url': link_sub_category,
                'answer': {'type': 'not-on-map'},
            },
        ]
        extra_properties_not_on_map_complex = [
            {
                'id': 'extra_straatverlichting_nummer',
                'label': 'Lichtpunt(en) op kaart',
                'category_url': link_sub_category,
                'answer': {
                    'id': '345345433',
                    'type': 'not-on-map',
                    'label': 'De container staat niet op de kaart - 345345433',
                },
            },
        ]
        extra_properties = [
            {
                'id': 'extra_straatverlichting_nummer',
                'label': 'Lichtpunt(en) op kaart',
                'category_url': link_sub_category,
                'answer': {
                    'id': '115617',
                    'type': '4',
                    'description': 'Overig lichtpunt',
                    'isReported': False,
                    'label': 'Overig lichtpunt - 115617',
                },
            },
        ]

        create_initial_data = copy.deepcopy(self.create_initial_data)
        create_initial_data.update({'category': {'category_url': link_sub_category}}),

        for invalid_extra_properties in [extra_properties_none, extra_properties_empty_list]:
            create_initial_data.update({'extra_properties': invalid_extra_properties})
            response = self.client.post(self.list_endpoint, create_initial_data, format='json')

            self.assertEqual(400, response.status_code)
            self.assertEqual(response.json()['extra_properties'][0],
                             'Extra properties not valid for category "lantaarnpaal-straatverlichting"')
            self.assertEqual(0, Signal.objects.count())

        signal_count = Signal.objects.count()
        for valid_extra_properties in [extra_properties_not_on_map_simple, extra_properties_not_on_map_complex,
                                       extra_properties]:
            create_initial_data.update({'extra_properties': valid_extra_properties})
            response = self.client.post(self.list_endpoint, create_initial_data, format='json')
            self.assertEqual(201, response.status_code)

            signal_count += 1
            self.assertEqual(signal_count, Signal.objects.count())
