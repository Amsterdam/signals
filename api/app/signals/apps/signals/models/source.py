from django.contrib.gis.db import models


class Source(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=3000)
    order = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ('order', 'name', )

    def __str__(self):
        return self.name
