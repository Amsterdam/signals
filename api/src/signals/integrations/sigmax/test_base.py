from django.test import TestCase

from datasets.external import base


class APITestHandler(base.BaseAPIHandler):
    name = 'test'

    def handle(self, signal):
        return True, 'test always works'

    def can_handle(self, signal):
        return True


class CannotHandler(base.BaseAPIHandler):
    name = 'cannot'

    def handle(self, signal):
        return True, 'test always works'

    def can_handle(self, signal):
        return False


class TestBaseAPIHandler(TestCase):
    def test_notimplemented(self):
        handler = base.BaseAPIHandler()

        self.assertEquals(handler.name, None)

        with self.assertRaises(NotImplementedError):
            handler.handle(None)

        with self.assertRaises(NotImplementedError):
            handler.can_handle(None)


class TestRegistration(TestCase):
    def test_no_registration(self):
        """Check that the correct fallback handler is registered."""
        base.reset_handlers()

        h = base.get_handler({'signal_id': 'Does not matter'})
        self.assertIsInstance(h, base.LogOnlyHandler)

    def test_registration_order(self):
        """Check that registration order."""
        base.reset_handlers()
        base.register_handler(APITestHandler)
        self.assertEqual(len(base._HANDLERS), 2)

        h = base.get_handler({'signal_id': 'Does not matter'})
        self.assertIsInstance(h, APITestHandler)

    def test_get_handlers(self):
        """Check that handler selection is done correctly."""
        base.reset_handlers()
        base.register_handler(APITestHandler)
        base.register_handler(CannotHandler)  # highest precedence, cannot handle signals

        h = base.get_handler({'signal_id': 'Does not matter'})
        self.assertIsInstance(h, APITestHandler)


class TestLogOnlyHandler(TestCase):
    def test_will_handle_any_signal(self):
        handler = base.LogOnlyHandler()
        self.assertTrue(handler.can_handle(None))
