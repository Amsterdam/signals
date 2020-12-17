from factory import DjangoModelFactory, Sequence, SubFactory, post_generation

from signals.apps.signals.models.signal_user import SignalUser


class SignalUserFactory(DjangoModelFactory):
    class Meta:
        model = SignalUser

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    user = SubFactory('signals.apps.users.factories.UserFactory')

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
