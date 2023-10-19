# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from factory import Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory

from signals.apps.signals.models.signal_user import SignalUser


class SignalUserFactory(DjangoModelFactory):
    class Meta:
        model = SignalUser
        skip_postgeneration_save = True

    _signal: SubFactory = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    user: SubFactory = SubFactory('signals.apps.users.factories.UserFactory')

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
        self.save()
