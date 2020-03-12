from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from change_log.tests.models import TestModel


class TestChangeLog(TestCase):
    """
    Pretty basic tests. Decided to add more tests when implementing the change_log on any of the models in the Signals
    app. So for now we only do a small tests to see if changes are logged on a "test only" model.

    The tests should be fixed if we decide to make this an stand-alone app.
    """
    def test_log(self):
        # Let's create a test_instance
        with freeze_time('2020-02-03T12:00:00'):
            test_instance = TestModel(title='The title')
            test_instance.save()

        # Update the title
        with freeze_time('2020-02-03T13:00:00'):
            test_instance.title = 'Title changed'
            test_instance.save()

            self.assertEqual(1, test_instance.logs.count())

            log_item = test_instance.logs.first()

            self.assertEqual(test_instance.pk, log_item.object_id)
            self.assertEqual('U', log_item.action)
            self.assertEqual(log_item.when, timezone.now())
            self.assertIsNone(log_item.who)

            self.assertEqual(2, len(log_item.data))
            self.assertEqual(log_item.data['id'], test_instance.pk)  # side-effect of the test only model
            self.assertEqual(log_item.data['title'], test_instance.title)

        # Update the title, text and active
        with freeze_time('2020-02-03T14:00:00'):
            test_instance.title = 'Changed title'
            test_instance.text = 'Some text we use for testing'
            test_instance.active = False
            test_instance.save()

            self.assertEqual(2, test_instance.logs.count())

            log_item = test_instance.logs.first()

            self.assertEqual(test_instance.pk, log_item.object_id)
            self.assertEqual('U', log_item.action)
            self.assertEqual(log_item.when, timezone.now())
            self.assertIsNone(log_item.who)

            self.assertEqual(4, len(log_item.data))
            self.assertEqual(log_item.data['id'], test_instance.pk)  # side-effect of the test only model
            self.assertEqual(log_item.data['title'], test_instance.title)
            self.assertEqual(log_item.data['text'], test_instance.text)
            self.assertEqual(log_item.data['active'], test_instance.active)
