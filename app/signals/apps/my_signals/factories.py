# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import factory
import faker
from factory.django import DjangoModelFactory

from signals.apps.my_signals.models import Token

fake = faker.Faker()


class TokenFactory(DjangoModelFactory):
    class Meta:
        model = Token

    reporter_email = factory.LazyAttribute(
        lambda o: fake.email()
    )
