"""
This migration is fixing the "is_responsible" and "can_view" flags (setting the to True) for all added
departments where these flags are currently False.
"""
from django.db import migrations

update_is_responsible = """
UPDATE signals_categorydepartment SET is_responsible = True WHERE is_responsible = False;
"""

update_can_view = """
UPDATE signals_categorydepartment SET can_view = True WHERE can_view = False;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0089_SIG-2117'),
    ]

    operations = [
        migrations.RunSQL(update_is_responsible),
        migrations.RunSQL(update_can_view),
    ]
