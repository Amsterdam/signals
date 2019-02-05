from django.contrib.gis.db import models
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

# Declaring custom Django signals for our `SignalManager`.
create_initial = DjangoSignal(providing_args=['signal_obj'])
add_image = DjangoSignal(providing_args=['signal_obj'])
update_location = DjangoSignal(providing_args=['signal_obj', 'location', 'prev_location'])
update_status = DjangoSignal(providing_args=['signal_obj', 'status', 'prev_status'])
update_category_assignment = DjangoSignal(providing_args=['signal_obj',
                                                          'category_assignment',
                                                          'prev_category_assignment'])
update_reporter = DjangoSignal(providing_args=['signal_obj', 'reporter', 'prev_reporter'])
update_priority = DjangoSignal(providing_args=['signal_obj', 'priority', 'prev_priority'])
create_note = DjangoSignal(providing_args=['signal_obj', 'note'])


class AttachmentManager(models.Manager):

    def get_attachments(self, signal):
        from signals.apps.signals.models import Attachment

        return Attachment.objects.filter(_signal=signal)

    def get_images(self, signal):
        from signals.apps.signals.models import Attachment

        return Attachment.objects.filter(_signal=signal, is_image=True)


class SignalManager(models.Manager):

    def create_initial(self,
                       signal_data,
                       location_data,
                       status_data,
                       category_assignment_data,
                       reporter_data,
                       priority_data=None):
        """Create a new `Signal` object with all related objects.

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :returns: Signal object
        """
        from .models import Location, Status, CategoryAssignment, Reporter, Priority

        with transaction.atomic():
            signal = self.create(**signal_data)

            # Set default (empty dict) value for `priority_data` if None is given.
            priority_data = priority_data or {}

            # Create dependent model instances with correct foreign keys to Signal
            location = Location.objects.create(**location_data, _signal_id=signal.pk)
            status = Status.objects.create(**status_data, _signal_id=signal.pk)
            category_assignment = CategoryAssignment.objects.create(**category_assignment_data,
                                                                    _signal_id=signal.pk)
            reporter = Reporter.objects.create(**reporter_data, _signal_id=signal.pk)
            priority = Priority.objects.create(**priority_data, _signal_id=signal.pk)

            # Set Signal to dependent model instance foreign keys
            signal.location = location
            signal.status = status
            signal.category_assignment = category_assignment
            signal.reporter = reporter
            signal.priority = priority
            signal.save()

            transaction.on_commit(lambda: create_initial.send(sender=self.__class__,
                                                              signal_obj=signal))

        return signal

    def add_image(self, image, signal):
        self.add_attachment(image, signal)
        add_image.send(sender=self.__class__, signal_obj=signal)

        return image

    def add_attachment(self, file, signal):
        from .models import Attachment

        with transaction.atomic():
            attachment = Attachment()
            attachment._signal = signal
            attachment.file = file

            # TODO do something with signal?
            attachment.save()

        return file

    def update_location(self, data, signal):
        """Update (create new) `Location` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Location object
        """
        from .models import Location

        with transaction.atomic():
            prev_location = signal.location

            location = Location.objects.create(**data, _signal_id=signal.id)
            signal.location = location
            signal.save()

            transaction.on_commit(lambda: update_location.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               location=location,
                                                               prev_location=prev_location))

        return location

    def update_status(self, data, signal):
        """Update (create new) `Status` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Status object
        """
        from .models import Status

        with transaction.atomic():
            status = Status(_signal=signal, **data)
            status.full_clean()
            status.save()

            prev_status = signal.status
            signal.status = status
            signal.save()

            transaction.on_commit(lambda: update_status.send(sender=self.__class__,
                                                             signal_obj=signal,
                                                             status=status,
                                                             prev_status=prev_status))

        return status

    def update_category_assignment(self, data, signal):
        """Update (create new) `CategoryAssignment` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Category object
        """
        from .models import CategoryAssignment

        with transaction.atomic():
            prev_category_assignment = signal.category_assignment

            category_assignment = CategoryAssignment.objects.create(**data, _signal_id=signal.id)
            signal.category_assignment = category_assignment
            signal.save()

            transaction.on_commit(lambda: update_category_assignment.send(
                sender=self.__class__,
                signal_obj=signal,
                category_assignment=category_assignment,
                prev_category_assignment=prev_category_assignment))

        return category_assignment

    def update_reporter(self, data, signal):
        """Update (create new) `Reporter` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Reporter object
        """
        from .models import Reporter

        with transaction.atomic():
            prev_reporter = signal.reporter

            reporter = Reporter.objects.create(**data, _signal_id=signal.id)
            signal.reporter = reporter
            signal.save()

            transaction.on_commit(lambda: update_reporter.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               reporter=reporter,
                                                               prev_reporter=prev_reporter))

        return reporter

    def update_priority(self, data, signal):
        """Update (create new) `Priority` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Priority object
        """
        from .models import Priority

        with transaction.atomic():
            prev_priority = signal.priority

            priority = Priority.objects.create(**data, _signal_id=signal.id)
            signal.priority = priority
            signal.save()

            transaction.on_commit(lambda: update_priority.send(sender=self.__class__,
                                                               signal_obj=signal,
                                                               priority=priority,
                                                               prev_priority=prev_priority))

        return priority

    def create_note(self, data, signal):
        """Create a new `Note` object for a given `Signal` object.

        :param data: deserialized data dict
        :returns: Note object
        """
        from .models import Note

        # Added for completeness of the internal API, and firing of Django
        # signals upon creation of a Note.
        with transaction.atomic():
            note = Note.objects.create(**data, _signal_id=signal.id)
            transaction.on_commit(lambda: create_note.send(sender=self.__class__,
                                                           signal_obj=signal,
                                                           note=note))

        return note
