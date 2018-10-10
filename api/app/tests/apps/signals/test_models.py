from unittest import mock

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from signals.apps.signals import workflow
from signals.apps.signals.models import (
    STADSDEEL_CENTRUM,
    CategoryAssignment,
    Location,
    Priority,
    Reporter,
    Signal,
    Status,
    get_address_text
)
from tests.apps.signals import factories, valid_locations


class TestSignalManager(TransactionTestCase):

    def setUp(self):
        sub_category = factories.SubCategoryFactory.create(name='Veeg- / zwerfvuil')

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
            'sub_category': sub_category,
        }
        self.status_data = {
            'state': workflow.GEMELD,
            'text': 'text message',
            'user': 'test@example.com',
        }
        self.priority_data = {
            'priority': Priority.PRIORITY_HIGH,
        }

    @mock.patch('signals.apps.signals.models.create_initial', autospec=True)
    def test_create_initial(self, patched_create_initial):
        # Create the full Signal
        signal = Signal.actions.create_initial(
            self.signal_data,
            self.location_data,
            self.status_data,
            self.category_assignment_data,
            self.reporter_data)

        # Check everything is present:
        self.assertEquals(Signal.objects.count(), 1)
        self.assertEquals(Location.objects.count(), 1)
        self.assertEquals(Status.objects.count(), 1)
        self.assertEquals(CategoryAssignment.objects.count(), 1)
        self.assertEquals(Reporter.objects.count(), 1)
        self.assertEquals(Priority.objects.count(), 1)

        # Check that we sent the correct Django signal
        patched_create_initial.send.assert_called_once_with(sender=Signal.actions.__class__,
                                                            signal_obj=signal)

    def test_create_initial_with_priority_data(self):
        signal = Signal.actions.create_initial(
            self.signal_data,
            self.location_data,
            self.status_data,
            self.category_assignment_data,
            self.reporter_data,
            self.priority_data)

        self.assertEqual(signal.priority.priority, Priority.PRIORITY_HIGH)

    @mock.patch('signals.apps.signals.models.update_location', autospec=True)
    def test_update_location(self, patched_update_location):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_location = signal.location
        location = Signal.actions.update_location(self.location_data, signal)

        # Check that the signal was updated in db
        self.assertEqual(signal.location, location)
        self.assertEqual(signal.locations.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_location.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            location=location,
            prev_location=prev_location)

    @mock.patch('signals.apps.signals.models.update_status', autospec=True)
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

        # Check that the signal status is updated
        self.assertEqual(signal.status, status)
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD)
        self.assertEqual(signal.statuses.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_status.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            status=status,
            prev_status=prev_status)

    @mock.patch('signals.apps.signals.models.update_category_assignment', autospec=True)
    def test_update_category_assignment(self, patched_update_category_assignment):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_category_assignment = signal.category_assignment
        category_assignment = Signal.actions.update_category_assignment(
            self.category_assignment_data, signal)

        # Check that the signal was updated in db
        self.assertEqual(signal.category_assignment, category_assignment)
        self.assertEqual(signal.sub_categories.count(), 2)

        # Check that we sent the correct Django signal
        patched_update_category_assignment.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            category_assignment=category_assignment,
            prev_category_assignment=prev_category_assignment)

    @mock.patch('signals.apps.signals.models.update_reporter', autospec=True)
    def test_update_reporter(self, patched_update_reporter):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_reporter = signal.reporter
        reporter = Signal.actions.update_reporter(self.reporter_data, signal)

        # Check that the signal was updated in db
        self.assertEqual(signal.reporter, reporter)
        self.assertEqual(signal.reporters.count(), 2)

        patched_update_reporter.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            reporter=reporter,
            prev_reporter=prev_reporter)

    @mock.patch('signals.apps.signals.models.update_priority')
    def test_update_priority(self, patched_update_priority):
        signal = factories.SignalFactory.create()

        # Update the signal
        prev_priority = signal.priority
        priority = Signal.actions.update_priority(self.priority_data, signal)

        # Check that the signal was updated in db
        self.assertEqual(signal.priority, priority)
        self.assertEqual(signal.priorities.count(), 2)

        patched_update_priority.send.assert_called_once_with(
            sender=Signal.actions.__class__,
            signal_obj=signal,
            priority=priority,
            prev_priority=prev_priority)


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
    @mock.patch('signals.apps.signals.models.isinstance', return_value=True)
    def test_get_fqdn_image_crop_url_with_swift_image(self, mocked_isinstance, mocked_url):
        mocked_url.return_value = 'https://objectstore.com/url/coming/from/swift/image.jpg'
        signal = factories.SignalFactoryWithImage.create()

        image_url = signal.get_fqdn_image_crop_url()

        self.assertEqual('https://objectstore.com/url/coming/from/swift/image.jpg', image_url)


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
        new_status = Status(_signal=self.signal, state=workflow.AFGEHANDELD, text='Done with it.')
        new_status.full_clean()
        new_status.save()

        self.assertTrue(new_status.id)

    def test_state_afgehandeld_text_required_invalid(self):
        new_status = Status(_signal=self.signal, state=workflow.AFGEHANDELD, text=None)

        with self.assertRaises(ValidationError) as error:
            new_status.full_clean()
        self.assertIn('text', error.exception.error_dict)


class TestCategoryDeclarations(TestCase):

    def test_main_category_string(self):
        main_category = factories.MainCategoryFactory.create(name='First category')

        self.assertEqual(str(main_category), 'First category')

    def test_sub_category_string(self):
        sub_category = factories.SubCategoryFactory.create(main_category__name='First category',
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
        address_text = get_address_text(self.location)

        self.assertEqual(correct, address_text)
        self.assertEqual(self.signal.location.address_text, address_text)

    def test_short_address_text(self):
        correct = 'Amstel 1'
        address_text = get_address_text(self.location, short=True)

        self.assertEqual(address_text, correct)
        self.assertEqual(self.signal.location.short_address_text, correct)

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

        correct = 'Sesamstraat 1A-achter 9999ZZ Amsterdam'
        self.assertEqual(get_address_text(self.location, short=False), correct)
