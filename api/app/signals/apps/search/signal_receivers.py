from django.dispatch import receiver

from signals.apps.search.tasks import save_to_elastic
from signals.apps.signals.managers import (
    create_child,
    create_initial,
    update_category_assignment,
    update_location,
    update_priority,
    update_type
)


@receiver([create_initial,
           create_child,
           update_location,
           update_category_assignment,
           update_priority,
           update_type], dispatch_uid='search_add_to_elastic')
def add_to_elastic_handler(sender, signal_obj, **kwargs):
    # Add to elastic
    save_to_elastic.delay(signal_id=signal_obj.id)
