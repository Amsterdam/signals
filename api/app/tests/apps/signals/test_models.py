import os
from unittest import mock

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import LiveServerTestCase, TestCase, TransactionTestCase
from django.utils import timezone
from django.utils.text import slugify

from signals.apps.signals import workflow
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
from signals.apps.signals.models.category_translation import CategoryTranslation
from tests.apps.signals import factories, valid_locations
from tests.apps.signals.attachment_helpers import small_gif


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
        old_updated_at = signal.updated_at

        # add note to signal via internal actions API
        note = Signal.actions.create_note(self.note_data, signal)

        # check that the note was added to the db
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(signal.notes.count(), 1)

        # signal updated_at field should be updated
        new_updated_at = Signal.objects.get(id=signal.id).updated_at
        self.assertNotEqual(old_updated_at, new_updated_at)

        # check that the relevant Django signal fired
        patched_create_note.send_robust.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            note=note)

    @mock.patch('signals.apps.signals.managers.create_child', autospec=True)
    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_split_signal(self, patched_update_status, patched_create_child):
        self.assertEqual(Signal.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(Status.objects.count(), 0)
        self.assertEqual(CategoryAssignment.objects.count(), 0)
        self.assertEqual(Priority.objects.count(), 0)

        parent_signal = factories.SignalFactory.create()
        prev_status = parent_signal.status

        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(Status.objects.count(), 1)
        self.assertEqual(CategoryAssignment.objects.count(), 1)
        self.assertEqual(Priority.objects.count(), 1)

        sub_cat = factories.CategoryFactory.create()

        Signal.actions.split(
            split_data=[
                {
                    'text': 'child #1',
                    'category': {
                        'sub_category': sub_cat,
                    }
                },
                {
                    'text': 'child #2',
                    'category': {
                        'sub_category': sub_cat,
                    }
                }
            ],
            signal=parent_signal
        )

        self.assertEqual(Signal.objects.count(), 3)
        self.assertEqual(Location.objects.count(), 3)
        self.assertEqual(Status.objects.count(), 4)
        self.assertEqual(CategoryAssignment.objects.count(), 3)
        self.assertEqual(Priority.objects.count(), 3)

        parent_signal.refresh_from_db()

        self.assertTrue(parent_signal.is_parent())
        self.assertFalse(parent_signal.is_child())
        self.assertEqual(parent_signal.children.count(), 2)
        self.assertEqual(parent_signal.status.state, workflow.GESPLITST)

        parent_signal_statusses = list(Status.objects.filter(_signal=parent_signal).order_by('id'))
        prev_status = parent_signal_statusses[0]
        status = parent_signal_statusses[1]

        patched_update_status.send_robust.assert_called_with(
            sender=Signal.actions.__class__,
            signal_obj=parent_signal,
            status=status,
            prev_status=prev_status)

        self.assertEqual(patched_create_child.send_robust.call_count, 2)


class TestSignalModel(TestCase):

    def test_sia_id(self):
        signal = factories.SignalFactory.create(id=999)

        self.assertEqual('SIA-999', signal.sia_id)

    def test_get_fqdn_image_crop_url_no_image(self):
        signal = factories.SignalFactory.create()

        image_url = signal.get_fqdn_image_crop_url()

        self.assertEqual(image_url, None)

    def test_get_fqdn_image_crop_url_with_local_image(self):
        Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={'domain': settings.SITE_DOMAIN, 'name': settings.SITE_NAME})
        signal = factories.SignalFactoryWithImage.create()

        image_url = signal.get_fqdn_image_crop_url()

        self.assertEqual('http://localhost:8000{}'.format(signal.image_crop.url), image_url)

    @mock.patch('imagekit.cachefiles.ImageCacheFile.url', new_callable=mock.PropertyMock)
    @mock.patch('signals.apps.signals.models.signal.isinstance', return_value=True)
    def test_get_fqdn_image_crop_url_with_swift_image(self, mocked_isinstance, mocked_url):
        mocked_url.return_value = 'https://objectstore.com/url/coming/from/swift/image.jpg'
        signal = factories.SignalFactoryWithImage.create()

        image_url = signal.get_fqdn_image_crop_url()

        mocked_isinstance.assert_called()
        self.assertEqual('https://objectstore.com/url/coming/from/swift/image.jpg', image_url)

    # Test for SIG-884

    def test_split_signal_add_first_child(self):
        signal = factories.SignalFactory.create()

        self.assertIsNone(signal.parent)  # No parent set

        signal.parent = factories.SignalFactory.create()
        signal.save()

        signal_from_db = Signal.objects.get(pk=signal.id)
        self.assertEqual(signal_from_db.parent_id, signal.parent_id)

        self.assertEqual(signal_from_db.siblings.count(), 0)  # Excluding the signal self
        self.assertEqual(signal_from_db.parent.children.count(), 1)  # All children of the parent

    def test_split_signal_cannot_be_parent_and_child(self):
        signal_parent = factories.SignalFactory.create()
        signal_children = factories.SignalFactory.create_batch(3, parent=signal_parent)
        signal_parent.parent = signal_children[0]

        with self.assertRaises(ValidationError) as cm:
            signal_parent.save()

        e = cm.exception
        self.assertEqual(e.message, 'Cannot be a parent and a child at the once')

    def test_split_signal_cannot_be_child_of_a_child(self):
        signal_parent = factories.SignalFactory.create()
        signal_children = factories.SignalFactory.create_batch(3, parent=signal_parent)

        signal = factories.SignalFactory.create()
        signal.parent = signal_children[0]

        with self.assertRaises(ValidationError) as cm:
            signal.save()

        e = cm.exception
        self.assertEqual(e.message, 'A child of a child is not allowed')

    def test_split_signal_max_children_reached(self):
        signal_parent = factories.SignalFactory.create()
        factories.SignalFactory.create_batch(3, parent=signal_parent)

        with self.assertRaises(ValidationError) as cm:
            factories.SignalFactory.create(parent=signal_parent)

        e = cm.exception
        self.assertEqual(e.message, 'Maximum number of children reached for the parent Signal')

    def test_split_signal_parent_status_cannot_change_from_gesplits(self):
        status_gesplitst = factories.StatusFactory.create(state=workflow.GESPLITST)
        signal_parent = factories.SignalFactory.create(status=status_gesplitst)
        factories.SignalFactory.create_batch(3, parent=signal_parent)

        status_behandeling = factories.StatusFactory.create(state=workflow.BEHANDELING)
        signal_parent.status = status_behandeling

        with self.assertRaises(ValidationError) as cm:
            signal_parent.save()

        e = cm.exception
        self.assertEqual(e.message, 'The status of a parent Signal can only be "gesplitst"')

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

    @mock.patch("uuid.uuid4")
    def test_uuid_assignment(self, mocked_uuid4):
        """ UUID should be assigned on construction of Signal """

        signal = Signal(signal_id=None)
        self.assertIsNotNone(signal.signal_id)
        mocked_uuid4.assert_called_once()


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
    doc_upload_location = os.path.join(os.path.dirname(__file__), 'sia-ontwerp-testfile.doc')
    json_upload_location = os.path.join(os.path.dirname(__file__), 'upload_standin.json')

    def setUp(self):
        self.signal = factories.SignalFactory.create()

        self.gif_upload = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')

    def test_cropping_image_cache_file(self):
        attachment = Attachment()
        attachment.file = self.gif_upload
        attachment._signal = self.signal
        attachment.mimetype = "image/gif"
        attachment.save()

        self.assertIsInstance(attachment.image_crop.url, str)
        self.assertTrue(attachment.image_crop.url.endswith(".jpg"))

        resp = requests.get(self.live_server_url + attachment.file.url)
        self.assertEqual(200, resp.status_code, "Original image is not reachable")

        resp = requests.get(self.live_server_url + attachment.image_crop.url)
        self.assertEqual(200, resp.status_code, "Cropped image is not reachable")

    def test_cache_file_with_word_doc(self):
        with open(self.doc_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("file.doc", f.read(), content_type="application/msword")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment.mimetype = "application/msword"
            attachment._signal = self.signal
            attachment.save()

        with self.assertRaises(Attachment.NotAnImageException):
            attachment.image_crop()

        resp = requests.get(self.live_server_url + attachment.file.url)
        self.assertEqual(200, resp.status_code, "Original file is not reachable")

    def test_cache_file_with_json_file(self):
        with open(self.json_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("upload.json", f.read(),
                                            content_type="application/json")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment.mimetype = "application/json"
            attachment._signal = self.signal
            attachment.save()

        with self.assertRaises(Attachment.NotAnImageException):
            attachment.image_crop()

        resp = requests.get(self.live_server_url + attachment.file.url)
        self.assertEqual(200, resp.status_code, "Original file is not reachable")

    def test_cache_file_without_mimetype(self):
        with open(self.json_upload_location, "rb") as f:
            doc_upload = SimpleUploadedFile("upload.json", f.read(),
                                            content_type="application/json")

            attachment = Attachment()
            attachment.file = doc_upload
            attachment._signal = self.signal
            attachment.save()

        with self.assertRaises(Attachment.NotAnImageException):
            attachment.image_crop()

        self.assertEqual("application/json", attachment.mimetype, "Mimetype should be set "
                                                                  "automatically when not set "
                                                                  "explicitly")

        resp = requests.get(self.live_server_url + attachment.file.url)
        self.assertEqual(200, resp.status_code, "Original file is not reachable")


class TestCategoryTranslation(TestCase):
    def setUp(self):
        self.category_1 = factories.CategoryFactory.create(is_active=True)
        self.category_2 = factories.CategoryFactory.create(is_active=True)
        self.category_not_active = factories.CategoryFactory.create(is_active=False)

    def test_create_translation(self):
        category_translation = CategoryTranslation.objects.create(
            old_category=self.category_1,
            new_category=self.category_2,
            text='Just a text we want to use',
            created_by='me@example.com',
        )

        self.assertEqual(category_translation.old_category, self.category_1)
        self.assertEqual(category_translation.new_category, self.category_2)
        self.assertEqual(category_translation.text, 'Just a text we want to use')
        self.assertEqual(category_translation.created_by, 'me@example.com')
        self.assertEqual(str(category_translation),
                         f'Zet categorie "{self.category_1.slug}" om naar "{self.category_2.slug}"')

    def test_create_translation_to_itself(self):
        with self.assertRaises(ValidationError) as cm:
            CategoryTranslation.objects.create(
                old_category=self.category_1,
                new_category=self.category_1,
                text='Just a text we want to use',
                created_by='me@example.com',
            )

        e = cm.exception
        self.assertEqual(e.messages[0], 'Cannot have old and new category the same.')

    def test_create_translation_to_inactive_category(self):
        with self.assertRaises(ValidationError) as cm:
            CategoryTranslation.objects.create(
                old_category=self.category_1,
                new_category=self.category_not_active,
                text='Just a text we want to use',
                created_by='me@example.com',
            )

        e = cm.exception
        self.assertEqual(e.messages[0], 'New category must be active')


class TestStatusMessageTemplate(TestCase):
    def setUp(self):
        self.category = factories.CategoryFactory.create(is_active=True)

    def test_save_too_many_instances(self):
        factories.StatusMessageTemplateFactory.create_batch(15, category=self.category, state='m')
        with self.assertRaises(ValidationError):
            StatusMessageTemplate.objects.create(
                category=self.category, state='m', title='title', text='text', order=999
            )

        qs = StatusMessageTemplate.objects.filter(category=self.category, state='m')
        self.assertEqual(qs.count(), 15)
