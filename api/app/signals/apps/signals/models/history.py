from django.contrib.gis.db import models

from signals.apps.signals.models.priority import Priority  # no circular imports ?
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

    @property
    def action(self):
        """Generate text for the action field that can serve as title in UI."""
        if self.what == 'UPDATE_STATUS':
            return 'Update status naar: {}'.format(
                dict(STATUS_CHOICES).get(self.extra, 'Onbekend'))
        elif self.what == 'UPDATE_PRIORITY':
            return 'Prioriteit update naar: {}'.format(
                dict(Priority.PRIORITY_CHOICES).get(self.extra, 'Onbekend'))
        elif self.what == 'UPDATE_CATEGORY_ASSIGNMENT':
            return 'Categorie gewijzigd naar: {}'.format(self.extra)
        elif self.what == 'CREATE_NOTE' or self.what == 'UPDATE_LOCATION':
            return self.extra
        elif self.what == 'RECEIVE_UPDATE':
            return 'Feedback van melder ontvangen'
        return 'Actie onbekend.'

    class Meta:
        managed = False
        db_table = 'signals_history_view'
