from django.db import migrations


def create_profile_for_users(apps, schema_editor):
    user_model = apps.get_model('auth', 'User')
    profile_model = apps.get_model('users', 'Profile')

    for user in user_model.objects.all():
        profile_model.objects.create(user=user)


def rollback_profile_creation(apps, schema_editor):
    profile_model = apps.get_model('users', 'Profile')
    profile_model.objects.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_profile_for_users, rollback_profile_creation),
    ]
