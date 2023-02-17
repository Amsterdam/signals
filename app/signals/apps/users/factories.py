# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
import factory
import faker
from django.conf import settings
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory

fake = faker.Faker()


class UserFactory(DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('username', )

    first_name = factory.LazyAttribute(
        lambda o: fake.first_name()
    )
    last_name = factory.LazyAttribute(
        lambda o: fake.last_name()
    )
    password = factory.LazyAttribute(
        lambda o: fake.password()
    )
    email = factory.LazyAttribute(
        lambda o: '{}.{}@example.com'.format(
            o.first_name.lower(),
            o.last_name.lower(),
        )
    )
    username = factory.LazyAttribute(
        lambda o: o.email
    )
    is_superuser = False
    is_staff = False


class SuperUserFactory(UserFactory):
    first_name = 'John'
    last_name = 'Doe'
    email = 'signals.admin@example.com'

    is_superuser = True
    is_staff = True


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.LazyAttribute(
        lambda o: fake.word()
    )
