# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
import factory
import faker
from django.conf import settings
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory

fake = faker.Faker()


def _generate_email(user) -> str:
    return '{}.{}@example.com'.format(
            user.first_name.lower(),
            user.last_name.lower(),
        )


def _generate_username(user) -> str:
    return user.email


class BaseUserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('username', )
        skip_postgeneration_save = True

    username = factory.LazyAttribute(_generate_username)
    password = factory.LazyFunction(fake.password)


class UserFactory(BaseUserFactory):
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    email = factory.LazyAttribute(_generate_email)

    is_superuser = False
    is_staff = False


class SuperUserFactory(BaseUserFactory):
    first_name = 'John'
    last_name = 'Doe'
    email = 'signals.admin@example.com'

    is_superuser = True
    is_staff = True


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)
        skip_postgeneration_save = True

    name = factory.LazyFunction(fake.word)
