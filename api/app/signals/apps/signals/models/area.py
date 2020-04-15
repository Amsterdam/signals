from django.db.models import F, Max, Min
from django.contrib.gis.db import models

# TODO: slugfields for the "code" fields below


class AreaManager(models.Manager):
    # Only show the most recent properties for an area
    def get_queryset(self):
        qs = super().get_queryset().annotate(
            updated_at=Max('properties__created_at'),
            created_at=Min('properties__created_at'),
        ).filter(
            properties__created_at=F('updated_at')
        )
        return qs


class AreaType(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    description = models.TextField(max_length=3000)


# Instances of Area are not to be edited after creation, in stead, their
# editable properties should be set by appendinng an AreaProperties instance
# pointing towards the relevant Area instance.
class Area(models.Model):
    class Meta:
        unique_together = ['code', 'type']

    code = models.CharField(max_length=255)
    type = models.ForeignKey(AreaType, on_delete=models.CASCADE)

    objects = AreaManager()


# Editable properties of an Area instance go here:
class AreaProperties(models.Model):
    name = models.CharField(max_length=255)
    area = models.ForeignKey(Area, related_name='properties', on_delete=models.CASCADE)
    geometry = models.MultiPolygonField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.EmailField(null=True, blank=True)
