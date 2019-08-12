from django.test import TestCase

from signals.utils.version import get_version


class TestVersion(TestCase):

    def test_get_version_full(self):
        version = (1, 2, 3)
        version_str = get_version(version)

        self.assertEqual(version_str, '1.2.3')

    def test_get_version_without_patch(self):
        version = (1, 3, 0)
        version_str = get_version(version)

        self.assertEqual(version_str, '1.3')

    def test_version(self):
        version_str = get_version()

        self.assertTrue(isinstance(version_str, str))
        self.assertTrue(len(version_str))
