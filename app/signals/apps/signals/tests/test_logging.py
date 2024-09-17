import logging

from django.urls import path
from rest_framework.test import APITestCase


def view_that_raises_exception(request):
    raise ValueError('Test exception')


urlpatterns = [
    path('test-exception/', view_that_raises_exception),
]


class MockHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class LoggingTestCase(APITestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.mock_handler = MockHandler()
        self.original_handlers = []

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            self.original_handlers.append(handler)

        self.logger.addHandler(self.mock_handler)

    def tearDown(self):
        self.logger.removeHandler(self.mock_handler)

        for handler in self.original_handlers:
            self.logger.addHandler(handler)

    def test_console_logging(self):
        test_message = 'Hello test world'
        self.logger.info(test_message)

        self.assertEqual(len(self.mock_handler.records), 1)
        self.assertEqual(self.mock_handler.records[0].getMessage(), test_message)

    def test_logging_level(self):
        self.logger.setLevel(logging.INFO)

        self.logger.debug('Debug message')
        self.logger.info('Info message')
        self.logger.error('Error message')
        self.logger.critical('Critical message')

        self.assertEqual(len(self.mock_handler.records), 3)
        self.assertEqual(self.mock_handler.records[0].levelname, 'INFO')
        self.assertEqual(self.mock_handler.records[1].levelname, 'ERROR')
        self.assertEqual(self.mock_handler.records[2].levelname, 'CRITICAL')
