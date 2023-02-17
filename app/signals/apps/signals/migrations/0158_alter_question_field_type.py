# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0157_new_subcategories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='field_type',
            field=models.CharField(
                choices=[
                    ('plain_text', 'PlainText'),
                    ('text_input', 'TextInput'),
                    ('multi_text_input', 'MultiTextInput'),
                    ('checkbox_input', 'CheckboxInput'),
                    ('radio_input', 'RadioInput'),
                    ('select_input', 'SelectInput'),
                    ('text_area_input', 'TextareaInput'),
                    ('asset_select', 'AssetSelect'),
                    ('location_select', 'LocationSelect')
                ],
                default='plain_text',
                max_length=32
            ),
        ),
    ]
