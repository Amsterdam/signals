# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0143_storedsignalfilter_show_on_overview'),
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
                    ('map_select', 'MapSelect'),
                    ('asset_select', 'AssetSelect')
                ],
                default='plain_text',
                max_length=32
            ),
        ),
    ]
