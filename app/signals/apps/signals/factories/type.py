# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from factory import SubFactory
from factory.django import DjangoModelFactory

from signals.apps.signals.models import Type


class TypeFactory(DjangoModelFactory):
    _signal: SubFactory = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    name = Type.SIGNAL  # Default type is a "Signal" (Melding in Dutch)

    class Meta:
        model = Type
        skip_postgeneration_save = True
