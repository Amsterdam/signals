from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.fields import AutoSlugField


class Category(models.Model):
    HANDLING_A3DMC = 'A3DMC'
    HANDLING_A3DEC = 'A3DEC'
    HANDLING_A3WMC = 'A3WMC'
    HANDLING_A3WEC = 'A3WEC'
    HANDLING_I5DMC = 'I5DMC'
    HANDLING_STOPEC = 'STOPEC'
    HANDLING_KLOKLICHTZC = 'KLOKLICHTZC'
    HANDLING_GLADZC = 'GLADZC'
    HANDLING_A3DEVOMC = 'A3DEVOMC'
    HANDLING_WS1EC = 'WS1EC'
    HANDLING_WS2EC = 'WS2EC'
    HANDLING_WS3EC = 'WS3EC'
    HANDLING_OND = 'ONDERMIJNING'
    HANDLING_REST = 'REST'
    HANDLING_EMPTY = 'EMPTY'
    HANDLING_LIGHTING = 'LIGHTING'
    HANDLING_GLAD_OLIE = 'GLAD_OLIE'
    HANDLING_CHOICES = (
        (HANDLING_A3DMC, HANDLING_A3DMC),
        (HANDLING_A3DEC, HANDLING_A3DEC),
        (HANDLING_A3WMC, HANDLING_A3WMC),
        (HANDLING_A3WEC, HANDLING_A3WEC),
        (HANDLING_I5DMC, HANDLING_I5DMC),
        (HANDLING_STOPEC, HANDLING_STOPEC),
        (HANDLING_KLOKLICHTZC, HANDLING_KLOKLICHTZC),
        (HANDLING_GLADZC, HANDLING_GLADZC),
        (HANDLING_A3DEVOMC, HANDLING_A3DEVOMC),
        (HANDLING_WS1EC, HANDLING_WS1EC),
        (HANDLING_WS2EC, HANDLING_WS2EC),
        (HANDLING_WS3EC, HANDLING_WS3EC),
        (HANDLING_REST, HANDLING_REST),
        (HANDLING_OND, HANDLING_OND),
        (HANDLING_EMPTY, HANDLING_EMPTY),
        (HANDLING_LIGHTING, HANDLING_LIGHTING),
        (HANDLING_GLAD_OLIE, HANDLING_GLAD_OLIE),
    )

    parent = models.ForeignKey('signals.Category',
                               related_name='children',
                               on_delete=models.PROTECT,
                               null=True, blank=True)

    # SIG-1135, the slug is auto populated using the django-extensions "AutoSlugField"
    slug = AutoSlugField(populate_from=['name', ], blank=False, overwrite=False, editable=False)

    name = models.CharField(max_length=255)
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES, default=HANDLING_REST)
    departments = models.ManyToManyField('signals.Department')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name',)
        unique_together = ('parent', 'slug',)
        verbose_name_plural = 'Categories'

    def __str__(self):
        """String representation."""
        return '{name}{parent}'.format(name=self.name,
                                       parent=" ({})".format(
                                           self.parent.name) if self.parent else ""
                                       )

    def is_parent(self):
        return self.children.exists()

    def is_child(self):
        return self.parent is not None

    def clean(self):
        super(Category, self).clean()

        if self.pk and self.slug:
            if not Category.objects.filter(id=self.pk, slug=self.slug).exists():
                raise ValidationError('Category slug cannot be changed')

        if self.is_parent() and self.is_child() or self.is_child() and self.parent.is_child():
            raise ValidationError('Category hierarchy can only go one level deep')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_translated(self):
        return (not self.is_active
                and self.translations.filter(new_category__is_active=True).exists())

    def translated_to(self):
        if self.is_translated():
            return self.translations.filter(
                new_category__is_active=True
            ).order_by(
                '-created_at'
            ).first().new_category
