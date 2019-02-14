from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test.testcases import TestCase

from tests.apps.users.factories import SuperUserFactory


class TestAdmin(TestCase):
    user = None
    group = None

    def setUp(self):
        self.user = SuperUserFactory()
        self.client.force_login(self.user)

        self.group = Group()
        self.group.save()

    @patch("signals.apps.signals.permissions.CategoryPermissions.create_for_all_categories")
    def test_call_create_categories_on_user_page_load(self, create_for_all_categories):
        response = self.client.get("/signals/admin/auth/user/{}/change/".format(self.user.id))
        self.assertEquals(200, response.status_code)

        create_for_all_categories.assert_called()

    @patch("signals.apps.signals.permissions.CategoryPermissions.create_for_all_categories")
    def test_call_create_categories_on_group_page_load(self, create_for_all_categories):
        response = self.client.get("/signals/admin/auth/group/{}/change/".format(self.group.id))
        self.assertEquals(200, response.status_code)

        create_for_all_categories.assert_called()
