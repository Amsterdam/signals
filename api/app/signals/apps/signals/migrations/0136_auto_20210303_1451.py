import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0135_delete_categorytranslation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='signal',
            old_name='signal_id',
            new_name='uuid',
        ),
        migrations.AlterField(
            model_name='signal',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.RemoveField(
            model_name='signal',
            name='upload',
        ),
    ]
