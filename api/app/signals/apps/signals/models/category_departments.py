from django.contrib.gis.db import models


class CategoryDepartment(models.Model):
    category = models.ForeignKey('signals.Category', on_delete=models.CASCADE)
    department = models.ForeignKey('signals.Department', on_delete=models.CASCADE)

    is_responsible = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_responsible:
            # If is_responsible is set to True than can_view must also be True
            self.can_view = True

        super(CategoryDepartment, self).save(*args, **kwargs)
