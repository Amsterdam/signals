import factory
import faker
from django.conf import settings
from django.contrib.auth.models import Group

from signals.apps.users.models import Profile

fake = faker.Faker()


class UserFactory(factory.DjangoModelFactory):

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


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.LazyAttribute(
        lambda o: fake.word()
    )


class UserProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile

    @factory.post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of groups were passed in, use them
            for department in extracted:
                self.departments.add(department)
