# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from factory import Sequence
from factory.django import DjangoModelFactory

from signals.apps.signals.models import Source


class SourceFactory(DjangoModelFactory):
    class Meta:
        model = Source

    name = Sequence(lambda n: f'Bron {n}')
    description = Sequence(lambda n: f'Beschrijving bron {n}')
    order = Sequence(lambda n: n)
    is_active = True
    is_public = False
    can_be_selected = True
