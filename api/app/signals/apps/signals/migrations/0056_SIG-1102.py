"""SIG-1102 Migrate ON_HOLD to INGEPLAND"""
from django.db import migrations, models

from signals.apps.signals import workflow


def migrate_on_hold(apps, schema_editor):
    Signal = apps.get_model('signals', 'Signal')
    Status = apps.get_model('signals', 'Status')

    on_hold_str = dict(workflow.STATUS_CHOICES).get(workflow.ON_HOLD)
    ingepland_str = dict(workflow.STATUS_CHOICES).get(workflow.INGEPLAND)
    message = 'Status `{}` afgevoerd en status `{}` ingevoerd'.format(on_hold_str, ingepland_str)

    on_hold_signals = Signal.objects.filter(status__state=workflow.ON_HOLD)
    for signal in on_hold_signals:
        status = Status(_signal=signal,
                        state=workflow.INGEPLAND,
                        text=message)
        status.full_clean()
        status.save()

        signal.status = status
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0055_extra_handling_messages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='status',
            name='state',
            field=models.CharField(blank=True,
                                   choices=[('m', 'Gemeld'), ('i', 'In afwachting van behandeling'),
                                            ('b', 'In behandeling'), ('h', 'On hold'),
                                            ('ingepland', 'Ingepland'),
                                            ('ready to send', 'Te verzenden naar extern systeem'),
                                            ('o', 'Afgehandeld'), ('a', 'Geannuleerd'),
                                            ('reopened', 'Heropend'), ('s', 'Gesplitst'),
                                            ('closure requested', 'Verzoek tot afhandeling'),
                                            ('sent', 'Verzonden naar extern systeem'), (
                                            'send failed',
                                            'Verzending naar extern systeem mislukt'), (
                                            'done external',
                                            'Melding is afgehandeld in extern systeem')],
                                   default='m', help_text='Melding status', max_length=20),
        ),
        migrations.RunPython(migrate_on_hold),
    ]
