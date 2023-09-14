# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
import os
from unittest import mock

from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import LiveServerTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django.utils.text import slugify

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import factories, workflow
from signals.apps.signals.models import (
    STADSDEEL_CENTRUM,
    Attachment,
    Category,
    CategoryAssignment,
    Location,
    Note,
    Priority,
    Reporter,
    Signal,
    Status,
    StatusMessageTemplate
)
from signals.apps.signals.tests import valid_locations
from signals.apps.signals.tests.attachment_helpers import small_gif


class TestSignalManager(TransactionTestCase):

    def setUp(self):
        sub_category = factories.CategoryFactory.create(name='Veeg- / zwerfvuil')

        # Deserialized data
        self.signal_data = {
            'text': 'text message',
            'text_extra': 'test message extra',
            'incident_date_start': timezone.now(),
        }
        self.location_data = {
            'geometrie': Point(4.898466, 52.361585),
            'stadsdeel': STADSDEEL_CENTRUM,
            'buurt_code': 'aaa1',
        }
        self.reporter_data = {
            'email': 'test_reporter@example.com',
            'phone': '0123456789',
        }
        self.category_assignment_data = {
            'category': sub_category,
        }
        self.status_data = {
            'state': workflow.GEMELD,
            'text': 'text message',
            'user': 'test@example.com',
        }
        self.priority_data = {
            'priority': Priority.PRIORITY_HIGH,
        }
        self.note_data = {
            'text': 'Dit is een test notitie.',
            'created_by': 'test@example.com',
        }

    @mock.patch('signals.apps.signals.managers.create_initial', autospec=True)
    def test_create_initial(self, patched_create_initial):
        # Create the full Signal
        signal = Signal.actions.create_initial(
            self.signal_data,
            self.location_data,
            self.status_data,
            self.category_assignment_data,
            self.reporter_data)

        # Check everything is present:
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(Status.objects.count(), 1)
        self.assertEqual(CategoryAssignment.objects.count(), 1)
        self.assertEqual(Reporter.objects.count(), 1)
        self.assertEqual(Priority.objects.count(), 1)

        # Check that we sent the correct Django signal
        patched_create_initial.send_robust.assert_called_once_with(sender=Signal.actions.__class__,
                                                                   signal_obj=signal)

    @mock.patch('signals.apps.signals.managers.create_initial', autospec=True)
    def test_create_initial_with_priority_data(self, patched_create_initial):
        signal = Signal.actions.create_initial(
            self.signal_data,
            self.location_data,
            self.status_data,
            self.category_assignment_data,
            self.reporter_data,
            self.priority_data)

        self.assertEqual(signal.priority.priority, Priority.PRIORITY_HIGH)

    @mock.patch('signals.apps.signals.managers.update_location', autospec=True)
    def test_update_location(self, patched_update_location):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_location = signal.location
        location = Signal.actions.update_location(self.location_data, signal)

        signal.refresh_from_db()

        # Check that the signal was updated in db
        self.assertEqual(signal.location, location)
        self.assertEqual(signal.locations.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_location.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            location=location,
            prev_location=prev_location)

    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    @mock.patch.object(Status, 'clean')
    def test_update_status(self, mocked_status_clean, patched_update_status):
        signal = factories.SignalFactory.create()
        prev_status = signal.status

        # Update status
        data = {
            'state': workflow.AFGEHANDELD,
            'text': 'Opgelost',
        }
        status = Signal.actions.update_status(data, signal)

        mocked_status_clean.assert_called_once()

        signal.refresh_from_db()

        # Check that the signal status is updated
        self.assertEqual(signal.status, status)
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD)
        self.assertEqual(signal.statuses.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_status.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            status=status,
            prev_status=prev_status)

    @mock.patch('signals.apps.signals.managers.update_category_assignment', autospec=True)
    def test_update_category_assignment(self, patched_update_category_assignment):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_category_assignment = signal.category_assignment
        category_assignment = Signal.actions.update_category_assignment(
            self.category_assignment_data, signal)

        signal.refresh_from_db()

        # Check that the signal was updated in db
        self.assertEqual(signal.category_assignment, category_assignment)
        self.assertEqual(signal.categories.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_category_assignment.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            category_assignment=category_assignment,
            prev_category_assignment=prev_category_assignment)

    def test_update_category_assignment_to_the_same_category(self):
        signal = factories.SignalFactory.create()

        category_assignment = Signal.actions.update_category_assignment(
            {
                'category': signal.category_assignment.category,
            },
            signal
        )

        self.assertIsNone(category_assignment)

    @mock.patch('signals.apps.signals.managers.update_reporter', autospec=True)
    def test_update_reporter(self, patched_update_reporter):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_reporter = signal.reporter
        reporter = Signal.actions.update_reporter(self.reporter_data, signal)

        signal.refresh_from_db()

        # Check that the signal was updated in db
        self.assertEqual(signal.reporter, reporter)
        self.assertEqual(signal.reporters.count(), 2)

        patched_update_reporter.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            reporter=reporter,
            prev_reporter=prev_reporter)

    @mock.patch('signals.apps.signals.managers.update_priority')
    def test_update_priority(self, patched_update_priority):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_priority = signal.priority
        priority = Signal.actions.update_priority(self.priority_data, signal)

        signal.refresh_from_db()

        # Check that the signal was updated in db
        self.assertEqual(signal.priority, priority)
        self.assertEqual(signal.priorities.count(), 2)

        patched_update_priority.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            priority=priority,
            prev_priority=prev_priority)

    @mock.patch('signals.apps.signals.managers.create_note')
    def test_create_note(self, patched_create_note):
        signal = factories.SignalFactory.create()

        # add note to signal via internal actions API
        note = Signal.actions.create_note(self.note_data, signal)

        # check that the note was added to the db
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(signal.notes.count(), 1)

        # check that the relevant Django signal fired
        patched_create_note.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            note=note)


class TestSignalModel(TestCase):

    def test_get_id_display(self):
        signal = factories.SignalFactory.create(id=999)
        self.assertEqual('SIG-999', signal.get_id_display())

        with override_settings(SIGNAL_ID_DISPLAY_PREFIX='SIGNALS-'):
            self.assertEqual('SIGNALS-999', signal.get_id_display())

        with override_settings(SIGNAL_ID_DISPLAY_PREFIX=''):
            self.assertEqual('999', signal.get_id_display())

        with override_settings(SIGNAL_ID_DISPLAY_PREFIX=None):
            self.assertEqual('999', signal.get_id_display())

    def test_sia_id(self):
        signal = factories.SignalFactory.create(id=999)

        self.assertEqual('SIA-999', signal.sia_id)

    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=3)
    def test_split_signal_add_first_child(self):
        signal = factories.SignalFactory.create()

        self.assertIsNone(signal.parent)  # No parent set

        signal.parent = factories.SignalFactory.create()
        signal.save()

        signal_from_db = Signal.objects.get(pk=signal.id)
        self.assertEqual(signal_from_db.parent_id, signal.parent_id)

        self.assertEqual(signal_from_db.siblings.count(), 0)  # Excluding the signal self
        self.assertEqual(signal_from_db.parent.children.count(), 1)  # All children of the parent

    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=3)
    def test_split_signal_cannot_be_parent_and_child(self):
        signal_parent = factories.SignalFactory.create()
        signal_children = factories.SignalFactory.create_batch(3, parent=signal_parent)
        signal_parent.parent = signal_children[0]

        with self.assertRaises(ValidationError) as cm:
            signal_parent.save()

        e = cm.exception
        self.assertEqual(e.message, 'Cannot be a parent and a child at the once')

    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=3)
    def test_split_signal_cannot_be_child_of_a_child(self):
        signal_parent = factories.SignalFactory.create()
        signal_children = factories.SignalFactory.create_batch(3, parent=signal_parent)

        signal = factories.SignalFactory.create()
        signal.parent = signal_children[0]

        with self.assertRaises(ValidationError) as cm:
            signal.save()

        e = cm.exception
        self.assertEqual(e.message, 'A child of a child is not allowed')

    @override_settings(SIGNAL_MAX_NUMBER_OF_CHILDREN=3)
    def test_split_signal_max_children_reached(self):
        signal_parent = factories.SignalFactory.create()
        factories.SignalFactory.create_batch(3, parent=signal_parent)

        with self.assertRaises(ValidationError) as cm:
            factories.SignalFactory.create(parent=signal_parent)

        e = cm.exception
        self.assertEqual(e.message, 'Maximum number of children reached for the parent Signal')

    def test_siblings_property(self):
        """ Siblings property should return siblings, not self """
        brother = factories.SignalFactory.create()
        sister = factories.SignalFactory.create()
        parent = factories.SignalFactory.create()

        brother.parent = parent
        brother.save()
        sister.parent = parent
        sister.save()

        self.assertEqual(1, brother.siblings.count())
        self.assertTrue(sister in brother.siblings)

        self.assertEqual(1, sister.siblings.count())
        self.assertTrue(brother in sister.siblings)

        sistah = factories.SignalFactory.create()
        sistah.parent = parent
        sistah.save()

        brother.refresh_from_db()
        self.assertEqual(2, brother.siblings.count())
        self.assertTrue(sister in brother.siblings)
        self.assertTrue(sistah in brother.siblings)

    def test_siblings_property_without_siblings(self):
        """ Should return an empty queryset. Not None """
        signal = factories.SignalFactory.create()
        self.assertEqual(0, signal.siblings.count())

    def test_to_str(self):
        signal = factories.SignalFactory.create()
        status = factories.StatusFactory.create(_signal=signal)

        location_data = {
            "geometrie": Point(4.9, 52.4),
            "buurt_code": "ABCD",
        }

        Signal.actions.update_location(location_data, signal)

        state = status.state
        signal.refresh_from_db()

        # Fix for bug SIG-2486 Timezones were not consistently shown
        created_at = signal.created_at.astimezone(timezone.get_current_timezone())

        self.assertEqual(f'{signal.id} - {state} - ABCD - {created_at.isoformat()}', signal.__str__())

    def test_allows_contact(self):
        """
        No feedback so needs to return True
        """
        signal = factories.SignalFactory.create()
        self.assertTrue(signal.allows_contact)

    def test_allows_contact_False(self):
        """
        Submitted feedback with allows_contantact False
        """
        signal = factories.SignalFactory.create()
        feedback = FeedbackFactory.create(
            _signal=signal,
            submitted_at='2022-01-01 00:00:00+00:00',
            allows_contact=False
        )
        feedback.save()
        self.assertFalse(signal.allows_contact)

    def test_allows_contact_True(self):
        """
        Submitted feedback with allows_contantact True
        """
        signal = factories.SignalFactory.create()
        feedback = FeedbackFactory.create(
            _signal=signal,
            submitted_at='2022-01-01 00:00:00+00:00',
            allows_contact=True
        )
        feedback.save()
        self.assertTrue(signal.allows_contact)

    def test_allows_contact_True_unsummited(self):
        """
        Unsubmitedd Feedback with Allows Contact True
        """
        signal = factories.SignalFactory.create()
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=True
        )
        feedback.save()
        self.assertTrue(signal.allows_contact)

    def test_allows_contact_False_unsummited(self):
        """
        Unsubmitedd Feedback with Allows Contact False
        """
        signal = factories.SignalFactory.create()
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=False
        )
        feedback.save()
        self.assertTrue(signal.allows_contact)

    @override_settings(FEATURE_FLAGS={
        'REPORTER_MAIL_CONTACT_FEEDBACK_ALLOWS_CONTACT_ENABLED': False,
    })
    def test_allowed_contact_disabled_flag(self):
        """
        When the flag is set to false the feature should always return true even if allows_contact is set to false
        """

        signal = factories.SignalFactory.create()
        feedback = FeedbackFactory.create(
            _signal=signal,
            allows_contact=False,
            submitted_at='2022-01-01 00:00:00+00:00'
        )
        feedback.save()
        self.assertTrue(signal.allows_contact)


class TestStatusModel(TestCase):

    def setUp(self):
        self.signal = factories.SignalFactory.create()
        self.status = self.signal.status
        self.assertEqual(self.status.state, workflow.GEMELD)

    def test_state_transition_valid(self):
        new_status = Status(_signal=self.signal, state=workflow.AFWACHTING)
        new_status.full_clean()
        new_status.save()

        self.assertTrue(new_status.id)

    def test_state_transition_invalid(self):
        new_status = Status(_signal=self.signal, state=workflow.VERZONDEN)

        with self.assertRaises(ValidationError) as error:
            new_status.full_clean()
        self.assertIn('state', error.exception.error_dict)

    def test_state_te_verzenden_required_target_api_valid(self):
        new_status = Status(_signal=self.signal,
                            state=workflow.TE_VERZENDEN,
                            target_api=Status.TARGET_API_SIGMAX)
        new_status.full_clean()
        new_status.save()

        self.assertTrue(new_status.id)

    def test_state_te_verzenden_required_target_api_invalid_empty_choice(self):
        new_status = Status(_signal=self.signal, state=workflow.TE_VERZENDEN, target_api=None)

        with self.assertRaises(ValidationError) as error:
            new_status.full_clean()
        self.assertIn('target_api', error.exception.error_dict)

    def test_state_transition_not_required_target_api(self):
        new_status = Status(_signal=self.signal,
                            state=workflow.ON_HOLD,
                            target_api=Status.TARGET_API_SIGMAX)

        with self.assertRaises(ValidationError) as error:
            new_status.full_clean()
        self.assertIn('target_api', error.exception.error_dict)

    def test_state_afgehandeld_text_required_valid(self):
        new_status = Status(_signal=self.signal, state=workflow.BEHANDELING, text='Working on it.')
        new_status.full_clean()
        new_status.save()

        self.signal.status = new_status
        self.signal.save()

        new_status = Status(_signal=self.signal, state=workflow.AFGEHANDELD, text='Done with it.')
        new_status.full_clean()
        new_status.save()

        self.assertTrue(new_status.id)

    def test_state_afgehandeld_text_required_invalid(self):
        new_status = Status(_signal=self.signal, state=workflow.AFGEHANDELD, text=None)

        with self.assertRaises(ValidationError) as error:
            new_status.full_clean()
        self.assertIn('text', error.exception.error_dict)


class TestCategory(TestCase):

    def setUp(self):
        self.category = factories.ParentCategoryFactory(name='Parent category')

    def test_is_parent(self):
        self.assertFalse(self.category.is_parent())

        child_category = factories.CategoryFactory(name='Child category')
        child_category.parent = self.category
        child_category.save()

        self.category.refresh_from_db()
        self.assertTrue(self.category.is_parent())

    def test_is_child(self):
        category = factories.CategoryFactory(name='Child category', parent=None)
        self.assertFalse(category.is_child())

        category.parent = self.category
        category.save()

        self.assertTrue(category.is_child())

    def test_category_two_deep(self):
        child_category = Category(name='Child category')
        child_category.parent = self.category
        child_category.save()

        self.category.refresh_from_db()
        self.assertEqual(1, self.category.children.count())

    def test_category_three_deep_as_grandchild(self):
        child_category = Category(name='Child category')
        child_category.parent = self.category
        child_category.save()

        grand_child_category = Category(name='Grandchild category')
        grand_child_category.parent = child_category

        self.assertRaises(ValidationError, grand_child_category.save)

    def test_category_three_deep_as_child(self):
        child_category = Category(name='Child category')
        child_category.save()

        grand_child_category = Category(name='Grandchild category')
        grand_child_category.parent = child_category
        grand_child_category.save()

        child_category.parent = self.category

        self.assertRaises(ValidationError, child_category.save)

    def test_slug_only_created_once(self):
        just_a_slug = slugify('just a slug')

        category = Category(slug=just_a_slug, name='This will generate the slug only once')

        category.save()
        category.refresh_from_db()

        slug = slugify(category.name)

        self.assertNotEqual(just_a_slug, category.slug)
        self.assertEqual(slug, category.slug)
        self.assertEqual('This will generate the slug only once', category.name)

        category.name = 'And now for something completely different'
        category.save()
        category.refresh_from_db()

        self.assertEqual(slug, category.slug)
        self.assertEqual('And now for something completely different', category.name)

        this_should_not_be_the_slug = slugify(category.name)
        self.assertNotEqual(this_should_not_be_the_slug, category.slug)

        with self.assertRaises(ValidationError):
            category.slug = just_a_slug
            category.save()

        with self.assertRaises(ValidationError):
            category.save(slug='no-saving-me-please')

    def test_child_category_configuration(self):
        """
        On a child category no additional configuration is allowed
        """
        parent_category = factories.ParentCategoryFactory(name='Parent category')
        child_category = factories.CategoryFactory(name='Child category', parent=parent_category)

        child_category.configuration = None
        child_category.save()  # should not raise a validation error

        child_category.configuration = {'no_configuration_allowed': True}
        with self.assertRaises(ValidationError):
            child_category.save()

    def test_valid_show_in_filter_parent_category_configuration(self):
        """
        On a parent category only the "show_children_in_filter" additional configuration is allowed.
        The "show_children_in_filter" should be a valid boolean value.
        """
        parent_category = factories.ParentCategoryFactory(name='Parent category')
        factories.CategoryFactory(name='Child category', parent=parent_category)

        parent_category.configuration = {'show_children_in_filter': True}
        parent_category.save()

        parent_category.configuration = {'show_children_in_filter': False}
        parent_category.save()

    def test_invalid_show_in_filter_parent_category_configuration(self):
        """
        On a parent category only the "show_children_in_filter" additional configuration is allowed.
        The "show_children_in_filter" should be a valid boolean value.
        """
        parent_category = factories.ParentCategoryFactory(name='Parent category')
        factories.CategoryFactory(name='Child category', parent=parent_category)

        configurations = [{'show_children_in_filter': 'True'},
                          {'show_children_in_filter': 'False'},
                          {'show_children_in_filter': ''},
                          {'show_children_in_filter': 123456},
                          {'show_children_in_filter': [True, ]},
                          {'show_children_in_filter': []},
                          {'show_children_in_filter': {'allowed': True}},
                          {'show_children_in_filter': {}}]

        for configuration in configurations:
            with self.subTest(configuration=configuration):
                parent_category.configuration = configuration
                with self.assertRaises(ValidationError) as e:
                    parent_category.save()

                validation_error = e.exception
                self.assertEqual(len(validation_error.error_dict['configuration']), 1)
                self.assertEqual(validation_error.error_dict['configuration'][0].message,
                                 'Value of "show_children_in_filter" is not a valid boolean')

    def test_only_show_in_filter_parent_category_configuration(self):
        """
        On a parent category only the "show_in_filter" additional configuration is allowed.
        The "show_in_filter" should be a valid boolean value and no additional configuration is allowed.
        """
        parent_category = factories.ParentCategoryFactory(name='Parent category')
        factories.CategoryFactory(name='Child category', parent=parent_category)

        parent_category.configuration = {'not': 'allowed'}

        with self.assertRaises(ValidationError) as e:
            parent_category.save()

        validation_error = e.exception
        self.assertEqual(validation_error.error_dict['configuration'][0].message,
                         'The "show_children_in_filter" is required for parent categories')

        parent_category.configuration = {'show_children_in_filter': True, 'not': 'allowed'}

        with self.assertRaises(ValidationError) as e:
            parent_category.save()

        validation_error = e.exception
        self.assertEqual(len(validation_error.error_dict['configuration']), 1)
        self.assertEqual(validation_error.error_dict['configuration'][0].message,
                         'Only "show_children_in_filter" is allowed')

    def test_invalid_show_in_filter_and_additional_config_parent_category_configuration(self):
        """
        On a parent category only the "show_children_in_filter" additional configuration is allowed.
        The "show_children_in_filter" should be a valid boolean value and no additional configuration is allowed.
        """
        parent_category = factories.ParentCategoryFactory(name='Parent category')
        factories.CategoryFactory(name='Child category', parent=parent_category)

        configurations = [{'show_children_in_filter': 'True', 'not': 'allowed'},
                          {'show_children_in_filter': 'False', 'not': 'allowed'},
                          {'show_children_in_filter': '', 'not': 'allowed'},
                          {'show_children_in_filter': 123456, 'not': 'allowed'},
                          {'show_children_in_filter': [True, ], 'not': 'allowed'},
                          {'show_children_in_filter': [], 'not': 'allowed'},
                          {'show_children_in_filter': {'allowed': True}, 'not': 'allowed'},
                          {'show_children_in_filter': {}, 'not': 'allowed'}]

        for configuration in configurations:
            with self.subTest(configuration=configuration):
                parent_category.configuration = configuration
                with self.assertRaises(ValidationError) as e:
                    parent_category.save()

                validation_error = e.exception
                self.assertEqual(len(validation_error.error_dict['configuration']), 2)
                messages = [ve.message for ve in validation_error.error_dict['configuration']]
                self.assertIn('Value of "show_children_in_filter" is not a valid boolean', messages)
                self.assertIn('Only "show_children_in_filter" is allowed', messages)


class TestCategoryDeclarations(TestCase):

    def test_main_category_string(self):
        main_category = factories.ParentCategoryFactory.create(name='First category')

        self.assertEqual(str(main_category), 'First category')

    def test_sub_category_string(self):
        sub_category = factories.CategoryFactory.create(parent__name='First category',
                                                        name='Sub')

        self.assertEqual(str(sub_category), 'Sub (First category)')

    def test_department_string(self):
        department = factories.DepartmentFactory.create(code='ABC', name='Department A')

        self.assertEqual(str(department), 'ABC (Department A)')


class GetAddressTextTest(TestCase):
    def setUp(self):
        self.signal = factories.SignalFactoryValidLocation.create()
        self.location = self.signal.location

        self.location.address = valid_locations.STADHUIS
        self.location.save()

    def test_full_address_text(self):
        correct = 'Amstel 1 1011PN Amsterdam'
        self.assertEqual(self.location.address_text, correct)

    def test_short_address_text(self):
        correct = 'Amstel 1'
        self.assertEqual(self.location.short_address_text, correct)

    def test_full_address_with_toevoeging(self):
        address = {
            'openbare_ruimte': 'Sesamstraat',
            'huisnummer': 1,
            'huisletter': 'A',
            'huisnummer_toevoeging': 'achter',
            'postcode': '9999ZZ',
            'woonplaats': 'Amsterdam',
        }
        self.location.address = address
        self.location.save()

        correct = 'Sesamstraat 1A-achter 9999ZZ Amsterdam'
        self.assertEqual(self.location.address_text, correct)


class TestAttachmentModel(LiveServerTestCase):
    doc_upload_location = os.path.join(os.path.dirname(__file__), 'test-data', 'sia-ontwerp-testfile.doc')
    json_upload_location = os.path.join(os.path.dirname(__file__), 'test-data', 'upload_standin.json')

    def setUp(self):
        self.signal = factories.SignalFactory.create()

        self.gif_upload = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

    def test_is_image_gif(self):
        attachment = Attachment()
        attachment.file = self.gif_upload
        attachment._signal = self.signal
        attachment.mimetype = "image/gif"
        attachment.save()

        self.assertTrue(attachment.is_image)

    def test_is_image_doc_provided(self):
        with open(self.doc_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("file.doc", f.read(), content_type="application/msword")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment.mimetype = "application/msword"
            attachment._signal = self.signal
            attachment.save()

            self.assertFalse(attachment.is_image)

    def test_is_image_doc_renamed_to_gif(self):
        with open(self.doc_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("file.gif", f.read(), content_type="application/msword")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment.mimetype = "application/msword"
            attachment._signal = self.signal
            attachment.save()

            self.assertFalse(attachment.is_image)


class TestStatusMessageTemplate(TestCase):
    @override_settings(STATUS_MESSAGE_TEMPLATE_MAX_INSTANCES=5)
    def test_save_too_many_instances(self):
        category = factories.CategoryFactory.create(is_active=True)
        factories.StatusMessageTemplateFactory.create_batch(5, category=category, state='m')

        with self.assertRaises(ValidationError):
            StatusMessageTemplate.objects.create(
                category=category, state='m', title='title', text='text', order=999
            )

        qs = StatusMessageTemplate.objects.filter(category=category, state='m')
        self.assertEqual(qs.count(), 5)
