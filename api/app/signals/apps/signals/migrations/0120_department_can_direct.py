from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0119_rename_eigen-organisatie_to_interne-melding'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='can_direct',
            field=models.BooleanField(default=False),
        ),
    ]
