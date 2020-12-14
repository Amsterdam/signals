from django.contrib.auth import get_user_model
from factory import DjangoModelFactory, Sequence, SubFactory, post_generation

from signals.apps.signals.models.signal_user import SignalUser

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = Sequence(lambda n: 'user{}@example.com'.format(n))
    username = Sequence(lambda n: 'user{}'.format(n))
    is_active = True


class SignalUserFactory(DjangoModelFactory):
    class Meta:
        model = SignalUser

    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    user = SubFactory('signals.apps.signals.factories.signal_user.UserFactory')

    @post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
