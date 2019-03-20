import json

from django.contrib.auth.models import Permission
from jsonschema import validate
from rest_framework.test import APITestCase

from signals.apps.signals import permissions
from tests.apps.users.factories import SuperUserFactory, UserFactory


class SIAReadPermissionMixin:
    _sia_read = None

    @property
    def sia_read(self):
        if self._sia_read is None:
            self._sia_read = Permission.objects.get(codename=permissions.SIA_READ)
        return self._sia_read


class SIAWritePermissionMixin:
    _sia_write = None

    @property
    def sia_write(self):
        if self._sia_write is None:
            self._sia_write = Permission.objects.get(codename=permissions.SIA_WRITE)
        return self._sia_write


class SIAAllCategoriesPermissionMixin:
    _sia_all_categories = None

    @property
    def sia_all_categories(self):
        if self._sia_all_categories is None:
            self._sia_all_categories = Permission.objects.get(
                codename=permissions.SIA_ALL_CATEGORIES)
        return self._sia_all_categories


class SuperUserMixin:
    @property
    def superuser(self):
        return SuperUserFactory.create()


class SimpleUserMixin:
    @property
    def user(self):
        return UserFactory.create(
            first_name='User',
            last_name='Simple',
        )


class SIAAllCategoriesUserMixin(SIAAllCategoriesPermissionMixin):
    @property
    def sia_all_categories_user(self):
        user = UserFactory.create(
            first_name='All Categories',
            last_name='User',
        )
        user.user_permissions.add(self.sia_all_categories)
        return user


class SIAReadUserMixin(SIAReadPermissionMixin):
    @property
    def sia_read_user(self):
        user = UserFactory.create(
            first_name='SIA-READ',
            last_name='User',
        )
        user.user_permissions.add(self.sia_read)
        return user


class SIAWriteUserMixin(SIAWritePermissionMixin):
    @property
    def sia_write_user(self):
        user = UserFactory.create(
            first_name='SIA-WRITE',
            last_name='USer',
        )
        user.user_permissions.add(self.sia_write)
        return user


class SIAReadWriteUserMixin(SIAReadPermissionMixin, SIAWritePermissionMixin):
    @property
    def sia_read_write_user(self):
        user = UserFactory.create(
            first_name='SIA-READ-WRITE',
            last_name='User',
        )
        user.user_permissions.add(self.sia_read)
        user.user_permissions.add(self.sia_write)
        return user


class SIAFullAccessUserMixin(SIAReadPermissionMixin,
                             SIAWritePermissionMixin,
                             SIAAllCategoriesPermissionMixin):
    @property
    def sia_full_access_user(self):
        user = UserFactory.create(
            first_name='SIA-FULL-ACCESS',
            last_name='User',
        )
        user.user_permissions.add(self.sia_read)
        user.user_permissions.add(self.sia_write)
        user.user_permissions.add(self.sia_all_categories)
        return user


class SignalsBaseApiTestCase(SuperUserMixin, SimpleUserMixin, APITestCase):
    def assertJsonSchema(self, schema: dict, json_dict: dict):
        """ Validates json_dict against schema. Schema format as defined on json-schema.org . If
        additionalProperties is not set in schema, it will be set to False. This assertion
        treats all properties as 'required', except for when required properties are explicitly
        set according to the json-schema.org standard """
        validate(instance=json_dict, schema=schema)

    @staticmethod
    def load_json_schema(filename: str):
        with open(filename) as f:
            return json.load(f)
