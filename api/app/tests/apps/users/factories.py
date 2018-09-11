import factory
from django.conf import settings


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL


class SuperUserFactory(UserFactory):
    first_name = 'John'
    last_name = 'Doe'
    email = 'signals.admin@amsterdam.nl'
    username = factory.LazyAttribute(lambda u: u.email)
    is_superuser = True
    is_staff = True

    class Meta:
        django_get_or_create = ('username', )
