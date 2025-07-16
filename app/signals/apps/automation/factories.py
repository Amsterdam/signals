# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

import factory
from faker import Faker
from factory import SubFactory
from signals.apps.automation.models import ForwardToExternal

fake = Faker()

class ForwardToExternalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ForwardToExternal
        skip_postgeneration_save = True

    expression: SubFactory = SubFactory('signals.apps.signals.factories.expression.ExpressionFactory')
    email: str = fake.email()
    text: str = fake.text()