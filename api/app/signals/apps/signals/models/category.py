from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


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
    HANDLING_REST = 'REST'
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
        (HANDLING_REST, HANDLING_REST),
    )

    parent = models.ForeignKey('signals.Category',
                               related_name='children',
                               on_delete=models.SET_NULL,
                               null=True)
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES, default=HANDLING_REST)
    departments = models.ManyToManyField('signals.Department')
    is_active = models.BooleanField(default=True)

    # Permission needed to access signals from this category (if user does not operate under the
    # SIA_ALL_CATEGORIES permission)
    permission = models.ForeignKey('auth.Permission',
                                   related_name='categories',
                                   on_delete=models.SET_NULL,
                                   null=True)

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

    def _validate(self):
        if self.is_parent() and self.is_child() or self.is_child() and self.parent.is_child():
            raise ValidationError('Category hierarchy can only go one level deep')

    def save(self, *args, **kwargs):
        self._validate()

        old_slug = self.slug
        self.slug = slugify(self.name)

        # Update permission name if new or category name updated
        if self.permission is not None and (old_slug != self.slug or not self.permission.name):
            self.permission.name = 'Category access - ' + self.name
            self.permission.save()

        super().save(*args, **kwargs)
