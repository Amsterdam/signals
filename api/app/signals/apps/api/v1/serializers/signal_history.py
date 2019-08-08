from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.feedback.models import Feedback
from signals.apps.signals.models import History, Location, Signal
from signals.apps.signals.models.location import get_address_text


def _get_description_of_update_location(obj):
    """Given a history entry for update location create descriptive text."""
    # Retrieve relevant location update object
    location_id = int(obj.identifier.strip('UPDATE_LOCATION_'))
    location = Location.objects.get(id=location_id)

    # Craft a message for UI
    desc = 'Stadsdeel: {}\n'.format(
        location.get_stadsdeel_display()) if location.stadsdeel else ''

    # Deal with address text or coordinates
    if location.address and isinstance(location.address, dict):
        field_prefixes = (
            ('openbare_ruimte', ''),
            ('huisnummer', ' '),
            ('huisletter', ''),
            ('huisnummer_toevoeging', '-'),
            ('woonplaats', '\n')
        )
        desc += get_address_text(location, field_prefixes)
    else:
        desc += 'Locatie is gepind op de kaart\n{}, {}'.format(
            location.geometrie[0],
            location.geometrie[1],
        )

    return desc


def _get_description_of_receive_feedback(obj):
    """Given a history entry for submission of feedback create descriptive text."""
    # Retrieve relevant location update object
    feedback_id = obj.identifier.strip('RECEIVE_FEEDBACK_')
    feedback = Feedback.objects.get(token=feedback_id)

    # Craft a message for UI
    desc = 'Ja, de melder is tevreden\n' if feedback.is_satisfied else \
        'Nee, de melder is ontevreden\n'
    desc += 'Waarom: {}'.format(feedback.text)

    if feedback.text_extra:
        desc += '\nToelichting: {}'.format(feedback.text_extra)

    yes_no = 'Ja' if feedback.allows_contact else 'Nee'
    desc += f'\nToestemming contact opnemen: {yes_no}'

    return desc


class HistoryHalSerializer(HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    who = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_who(self, obj):
        """Generate string to show in UI, missing users are set to default."""
        if obj.who is None:
            return 'SIA systeem'
        return obj.who

    def get_description(self, obj):
        if obj.what == 'UPDATE_LOCATION':
            return _get_description_of_update_location(obj)
        elif obj.what == 'RECEIVE_FEEDBACK':
            return _get_description_of_receive_feedback(obj)
        else:
            return obj.description

    class Meta:
        model = History
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )
