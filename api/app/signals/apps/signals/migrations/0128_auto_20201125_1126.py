import django.db.models.manager
from django.db import migrations, models

SQL = '''
UPDATE signals_signal
SET type_assignment_id = sub.max_type_id
FROM (
    SELECT MAX(st.id) AS max_type_id, st._signal_id
    FROM signals_type AS st
    GROUP BY st._signal_id
) AS sub
WHERE id = sub._signal_id
'''

REVERSE_SQL = '''
UPDATE signals_signal
SET type_assignment_id = NULL
'''


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0127_routingexpression'),
    ]

    operations = [
        migrations.AddField(
            model_name='signal',
            name='type_assignment',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signal',
                                       to='signals.Type'),
        ),
        migrations.RunSQL(SQL, REVERSE_SQL)
    ]
