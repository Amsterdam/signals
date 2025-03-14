from django.db import models


class Relation(models.Model):
    source=models.ForeignKey('signals.Signal', related_name='source_signal', on_delete=models.CASCADE)
    target=models.ForeignKey('signals.Signal', related_name='target_signal', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('source', 'target')
