from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import path
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from rest_framework.test import APITestCase


def view_that_raises_exception(request):
    raise ValueError("Test exception")


urlpatterns = [
    path("test-exception/", view_that_raises_exception),
]


class MockSpanProcessor(SimpleSpanProcessor):
    """
    A mock like span processor
    """

    def __init__(self):
        self.spans = []

    def on_end(self, span):
        self.spans.append(span)

    def shutdown(self):
        pass  # Avoid AttributeError during teardown


class SpanCreationTestCase(APITestCase):

    def setUp(self):
        self.test_span_processor = MockSpanProcessor()
        tracer_provider = trace.get_tracer_provider()
        tracer_provider.add_span_processor(self.test_span_processor)

    def test_span_creation(self):
        """
        Test if the app succesfully creates spans by creating a
        custom trace and performing a query inside it.
        """

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("test_span"):
            User.objects.all().count()

        self.assertTrue(
            len(self.test_span_processor.spans) > 0, "No spans were created"
        )

        # Find the span for the database query
        db_span = next(
            (span for span in self.test_span_processor.spans if span.name == "SELECT"),
            None,
        )
        self.assertIsNotNone(db_span, "No SELECT span found")

        if db_span:
            self.assertIn("db.system", db_span.attributes)
            self.assertEqual(db_span.attributes["db.system"], "postgresql")

        root_span = next(
            (
                span
                for span in self.test_span_processor.spans
                if span.name == "test_span"
            ),
            None,
        )
        self.assertIsNotNone(root_span, "No root span found")

        if root_span:
            self.assertEqual(
                root_span.resource.attributes["service.name"],
                settings.MONITOR_SERVICE_NAME,
            )

    def test_response_hook(self):
        """
        For every authenticated request there should be a username and id attached through the response hook.
        """

        user = User.objects.create_user(username="testuser", password="12345")
        client = Client()
        client.login(username="testuser", password="12345")

        client.get("/status/health")

        self.assertTrue(
            len(self.test_span_processor.spans) > 0, "No spans were created"
        )

        # Find the span created from performing a GET request
        request_span = next(
            (
                span
                for span in self.test_span_processor.spans
                if "http.method" in span.attributes
                and span.attributes["http.method"] == "GET"
            ),
            None,
        )
        self.assertIsNotNone(request_span, "No request span found")

        if request_span:
            self.assertIn("user_id", request_span.attributes)
            self.assertEqual(request_span.attributes["user_id"], user.id)
            self.assertEqual(request_span.attributes["username"], user.username)

    @override_settings(ROOT_URLCONF=__name__)
    def test_exception_logging_with_traceback(self):
        user = User.objects.create_user(username="testuser", password="12345")
        client = Client()
        client.login(username=user.username, password=user.password)

        with self.assertRaises(ValueError), self.assertLogs(
            level="ERROR"
        ) as log_context:
            client.get("/test-exception/")

        self.assertTrue(
            any("ValueError: Test exception" in log for log in log_context.output)
        )
        self.assertTrue(
            any(
                "Traceback (most recent call last):" in log
                for log in log_context.output
            )
        )

        request_span = next(
            (
                span
                for span in self.test_span_processor.spans
                if "http.method" in span.attributes
                and span.attributes["http.method"] == "GET"
            ),
            None,
        )
        self.assertIsNotNone(request_span, "No request span found")
        self.assertEqual(request_span.name, "GET test-exception/")
        self.assertEqual(request_span.attributes["http.status_code"], 500)
