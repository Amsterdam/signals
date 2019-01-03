"""
Models to help keep track of state of communication with Sigmax.

Context: in previous versions of the SIA - CityControl integration, we assured a
`Signal` instance can only be sent to CityControl once through checks on the
workflow. The new requirement that though resolved a `Signal` should be able to
be reopened. This implies that a `Signal` can be sent to Sigmax mutiple times
and a new naming scheme in CityControl is needed.

The new scheme is as follows: SIA-123.01, SIA-123.02, ...

Since a re-opened `Signal` may not have been sent to CityControl previously. So
counting the number of re-openings (or start states) of a `Signal` is not enough
to produce the sequence number. We have to count how many times a `Signal` was
sent to CityControl previously (and keep that logic out of the core SIA
application).
"""
from django.db import models

from signals.apps.signals.models import Signal


class CityControlRoundtrip(models.Model):
    """Use this model to record when a `Signal` was sent to Sigmax."""
    _signal = models.ForeignKey(
        Signal,
        related_name='citycontrol_roundtrips+',
        on_delete=models.CASCADE,
    )
    when = models.DateTimeField(editable=False, auto_now_add=True)
