from django.contrib.gis.db import models


class ExternalTDO(models.Model):
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
