from django.contrib.gis.db import models


class Type(models.Model):
    SIGNAL = 'SIG'  # Melding
    REQUEST = 'REQ'  # Aanvraag
    QUESTION = 'QUE'  # Vraag
    COMPLAINT = 'COM'  # Klacht
    MAINTENANCE = 'MAI'  # Groot onderhoud

    CHOICES = (
        (SIGNAL, 'Signal'),  # Melding
        (REQUEST, 'Request'),  # Aanvraag
        (QUESTION, 'Question'),  # Vraag
        (COMPLAINT, 'Complaint'),  # Klacht
        (MAINTENANCE, 'Maintenance'),  # Groot onderhoud
    )

    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='types')
    name = models.CharField(max_length=3, choices=CHOICES, default=SIGNAL)

    created_by = models.EmailField(null=True, blank=True)  # null will default to the system user
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    class Meta:
        ordering = ('_signal', '-created_at', )
        verbose_name_plural = 'Types'

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Type, self).save(*args, **kwargs)


def _history_translated_action(name):
    translated = {
        Type.SIGNAL: 'Melding',
        Type.REQUEST: 'Aanvraag',
        Type.QUESTION: 'Vraag',
        Type.COMPLAINT: 'Klacht',
        Type.MAINTENANCE: 'Groot onderhoud',
    }
    return translated[name]
