"""Add uniqueness constraints to Area and AreaType models."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0107_category_changes_sig-2627'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='area',
            options={'verbose_name': 'Gebied', 'verbose_name_plural': 'Gebieden'},
        ),
        migrations.AlterModelOptions(
            name='areatype',
            options={'verbose_name': 'Gebiedstype', 'verbose_name_plural': 'Gebiedstypen'},
        ),
        migrations.AlterField(
            model_name='areatype',
            name='code',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='area',
            unique_together={('code', '_type')},
        ),
    ]
