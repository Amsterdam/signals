from django.contrib.gis.db import models


class TDOSignal(models.Model):
    """
    This model exposes a database view and therefore has the "managed = False" property.

    The view exposes SIA data for teamdata openbare ruimte, as a temporary solution it is also possible to export this
    data via a management command by CSV to the teamdata openbare ruimte ObjectStore.
    """
    class Meta:
        managed = False
        db_table = 'signals_ext_tdo'

    id = models.IntegerField(primary_key=True)
    created_at = models.DateTimeField(null=False)
    updated_at = models.DateTimeField(null=False)
    geometry = models.PointField(name='geometry')
    status = models.CharField(max_length=255)
    main_slug = models.CharField(max_length=255)
    sub_slug = models.CharField(max_length=255)
