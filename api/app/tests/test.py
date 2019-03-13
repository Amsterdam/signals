import json

from django.contrib.auth.models import Permission
from jsonschema import validate
from rest_framework.test import APITestCase

from tests.apps.users.factories import SuperUserFactory, UserFactory


class SIAReadPermissionMixin:
    _sia_read = None

    @property
    def sia_read(self):
        if self._sia_read is None:
            self._sia_read = Permission.objects.get(codename='sia_read')
        return self._sia_read


class SIAWritePermissionMixin:
    _sia_write = None

    @property
    def sia_write(self):
        if self._sia_write is None:
            self._sia_write = Permission.objects.get(codename='sia_write')
        return self._sia_write


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


class SIAReadUserMixin(SIAReadPermissionMixin):
    @property
    def sia_read_user(self):
        user = UserFactory.create(
            first_name='SIA-READ',
            last_name='User',
        )
        user.user_permissions.add(self.sia_read)
        return user


class SIAWriteUserMixin(SIAReadPermissionMixin, SIAWritePermissionMixin):
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
