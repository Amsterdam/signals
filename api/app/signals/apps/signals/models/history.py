from django.contrib.gis.db import models

from signals.apps.feedback.models import _get_description_of_receive_feedback
from signals.apps.signals.models.location import _get_description_of_update_location
from signals.apps.signals.models.type import _history_translated_action
from signals.apps.signals.workflow import STATUS_CHOICES


class History(models.Model):
    identifier = models.CharField(primary_key=True, max_length=255)
    _signal = models.ForeignKey('signals.Signal',
                                related_name='history',
                                null=False,
                                on_delete=models.CASCADE)
    when = models.DateTimeField(null=True)
    what = models.CharField(max_length=255)
    who = models.CharField(max_length=255, null=True)  # old entries in database may have no user
    extra = models.CharField(max_length=255, null=True)  # not relevant for every logged model.
    description = models.TextField(max_length=3000)

    # No changes to this database view please!
    def save(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    def get_action(self):
        """Generate text for the action field that can serve as title in UI."""
        if self.what == 'UPDATE_STATUS':
            return f'Update status naar: {dict(STATUS_CHOICES).get(self.extra, "Onbekend")}'
        elif self.what == 'UPDATE_PRIORITY':
            # SIG-1727 ad-hoc translation, must match signals.Priority model!
            translated = {'high': 'Hoog', 'normal': 'Normaal', 'low': 'Laag'}.get(self.extra, 'Onbekend')
            return f'Urgentie update naar: {translated}'
        elif self.what == 'UPDATE_CATEGORY_ASSIGNMENT':
            return f'Categorie gewijzigd naar: {self.extra}'
        elif self.what == 'CREATE_NOTE' or self.what == 'UPDATE_LOCATION':
            return self.extra
        elif self.what == 'RECEIVE_FEEDBACK':
            return 'Feedback van melder ontvangen'
        elif self.what == 'UPDATE_TYPE_ASSIGNMENT':
            return f'Type update naar: {_history_translated_action(self.extra)}'
        elif self.what == 'UPDATE_DIRECTING_DEPARTMENTS_ASSIGNMENT':
            return f'Regie voerende afdeling/afdelingen gewijzigd naar: {self.extra}'
        return 'Actie onbekend.'

    def get_who(self):
        """Generate string to show in UI, missing users are set to default."""
        if self.who is None:
            return 'SIA systeem'
        return self.who

    def get_description(self):
        if self.what == 'UPDATE_LOCATION':
            location_id = int(self.identifier.strip('UPDATE_LOCATION_'))
            return _get_description_of_update_location(location_id)
        elif self.what == 'RECEIVE_FEEDBACK':
            feedback_id = self.identifier.strip('RECEIVE_FEEDBACK_')
            return _get_description_of_receive_feedback(feedback_id)
        else:
            return self.description

    class Meta:
        managed = False
        db_table = 'signals_history_view'
