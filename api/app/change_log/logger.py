import json
import threading

from django.contrib.contenttypes.models import ContentType
from django.db import models

from change_log.models import Log
from change_log.tracker import ChangeTracker


@property
def logs(self):
    # This will be added to the model the logger is declared on so that we have a way to access the change log from the
    # instance
    content_type = ContentType.objects.get_for_model(self)
    return Log.objects.filter(object_id=self.pk, content_type=content_type)


class ChangeLogger:
    """
    !!! Bulk operations are not supported by this implementation !!!
    """
    # The ChangeLoggerMiddleware will place the request on this thread so that we can get the user from it
    thread = threading.local()

    def __init__(self, tracker_class=None):
        self._tracker_class = tracker_class or ChangeTracker

    def contribute_to_class(self, cls, name, **kwargs):
        """
        The Django model will call the 'contribute_to_class' method for each of the attributes ending up in the model.

        So this way we can add some functionality to the model without overriding it in some baseclass. This is done
        a lot in the Django ORM. For example the DateField will add the functions 'get_next_by_date' and
        'get_previous_by_date' to the model where these fields are defined.
        """
        self.model = cls
        self.name = name

        setattr(cls, name, self)
        setattr(cls, 'logs', logs)

        models.signals.post_init.connect(self.initialize_logger)

    def initialize_logger(self, sender, instance, **kwargs):
        if not isinstance(instance, self.model):
            # Only initialize for instances that are an instance of the model that the logger is declared on
            return

        tracker = self._tracker_class(instance=instance)
        setattr(instance, '_change_tracker', tracker)
        tracker.store_state()

        self.patch_save(instance)

    def patch_save(self, instance):
        # We keep the original save because we still call it to store data. We only add the functionality that will
        # add the row in the change_log table
        original_save = instance.save

        def save(**kwargs):
            # Check to see if the object is inserted or updated
            created = instance.pk is None

            # Call the original save function
            original_save_return = original_save(**kwargs)

            tracker = getattr(instance, '_change_tracker')
            instance_changed = tracker.instance_changed

            if created or not created and instance_changed:
                who = None
                if hasattr(self.thread, 'request'):
                    who = self.thread.request.user.email if hasattr(self.thread.request, 'user') else None
                Log.objects.create(
                    object=instance,
                    action='I' if created else 'U',
                    who=who,
                    data=json.dumps(tracker.changed_data())
                )

            return original_save_return

        instance.save = save
