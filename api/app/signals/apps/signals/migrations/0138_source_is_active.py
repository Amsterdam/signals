# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.db import migrations, models


def activate_sources(apps, schema_editor):
    """
    Make sure all sources in the system are active

    :param apps:
    :param schema_editor:
    :return:
    """
    Source = apps.get_model('signals', 'Source')
    Source.objects.update(is_active=True)


def _add_sources(apps, schema_editor):
    """
    Add unknown sources present in Signal.source to the sources table. These sources are not active by default

    :param apps:
    :param schema_editor:
    :return:
    """
    Signal = apps.get_model('signals', 'Signal')
    Source = apps.get_model('signals', 'Source')

    order_qs = Source.objects.order_by('-order').only('order')
    if order_qs.exists():
        max_order = order_qs.first().order
    else:
        max_order = 0

    signal_sources = Signal.objects.values_list('source', flat=True).distinct('source').order_by('source')
    for signal_source in signal_sources:
        source, created = Source.objects.get_or_create(
            name=signal_source,
            defaults={'description': signal_source, 'is_active': False}
        )
        if created:
            max_order += 1
            source.order = max_order
            source.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0137_auto_20210303_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(activate_sources, lambda x, y: True),  # noqa No reverse needed because the is_active flag will be removed
        migrations.RunPython(_add_sources, lambda x, y: True),  # No reverse possible
    ]
