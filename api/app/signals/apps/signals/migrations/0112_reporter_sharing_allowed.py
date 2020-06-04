from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0111_fix_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='reporter',
            name='sharing_allowed',
            field=models.BooleanField(default=False),
        ),
    ]
