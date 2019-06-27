"""
SIG-1361
"""
from django.db import migrations
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

STRAATVERLICHTING_URL = '/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting'  # noqa: 501
RELEVANT_QUESTION_ID = 'extra_straatverlichting_niet_op_kaart_nummer'
RELEVANT_QUESTION_LABEL = 'Selecteer het lichtpunt waar het om gaat'

# The following JSON schema matches "bad" question/answer entries in the
# extra_properties field for Signals concerning streetlights.
SCHEMA_BAD_ENTRIES = {
        '$schema': 'http://json-schema.org/schema#',
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
            },
            'answer': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {
                            'type': 'string',
                        },
                        'label': {
                            'type': 'string',
                            'minLength': 1,
                        }
                    }
                }
            },
            'category_url': {
                'type': 'string',
            },
            'label': {
                'type': 'string',
            }
        }
    }


def migrate_data(apps, schema_editor):
    """
    Migrate the extra properties where lantarn numbers are in incorrect data format.
    """
    Signal = apps.get_model('signals', 'Signal')
    schema_validator = Draft7Validator(schema=SCHEMA_BAD_ENTRIES)

    straatverlichting = (
        Signal.objects.filter(
            category_assignment__category__slug='lantaarnpaal-straatverlichting'
        ).filter(
            extra_properties__isnull=False
        )
    )

    for signal in straatverlichting:
        mutated_properties = []  # will contain mutated copy of extra_properties
        selected_lights = []

        for qa_entry in signal.extra_properties:
            try:
                schema_validator.validate(qa_entry)
            except ValidationError:
                mutated_properties.append(qa_entry)
                continue

            if (qa_entry['category_url'] == STRAATVERLICHTING_URL and
                    qa_entry['id'] == RELEVANT_QUESTION_ID):
                for selected_light in qa_entry['answer']:
                    selected_lights.append(selected_light['label'])
            else:
                mutated_properties.append(qa_entry)
        else:
            if selected_lights:
                new_qa_entry = {
                    'id': RELEVANT_QUESTION_ID,
                    'category_url': STRAATVERLICHTING_URL,
                    'label': RELEVANT_QUESTION_LABEL,
                    'answer': selected_lights,
                }
                mutated_properties.append(new_qa_entry)

        signal.extra_properties = mutated_properties
        signal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0065_auto_20190618_0839'),
    ]

    operations = [
        migrations.RunPython(migrate_data),
    ]
