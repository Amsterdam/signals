from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

# Declaring custom Django signals for our `SignalManager`.
create_initial = DjangoSignal(providing_args=['signal_obj'])
create_child = DjangoSignal(providing_args=['signal_obj'])
add_image = DjangoSignal(providing_args=['signal_obj'])
add_attachment = DjangoSignal(providing_args=['signal_obj'])
update_location = DjangoSignal(providing_args=['signal_obj', 'location', 'prev_location'])
update_status = DjangoSignal(providing_args=['signal_obj', 'status', 'prev_status'])
update_category_assignment = DjangoSignal(providing_args=['signal_obj',
                                                          'category_assignment',
                                                          'prev_category_assignment'])
update_reporter = DjangoSignal(providing_args=['signal_obj', 'reporter', 'prev_reporter'])
update_priority = DjangoSignal(providing_args=['signal_obj', 'priority', 'prev_priority'])
create_note = DjangoSignal(providing_args=['signal_obj', 'note'])


def send_signals(to_send):
    """
    Helper function, sends properly instantiated Django Signals.

    :param to_send: list of tuples of django signal definition and keyword arguments
    """
    for django_signal, kwargs in to_send:
        django_signal.send_robust(**kwargs)


class SignalManager(models.Manager):

    def _create_initial_no_transaction(self, signal_data, location_data, status_data,
                                       category_assignment_data, reporter_data, priority_data=None):
        """Create a new `Signal` object with all related objects.
            If a transaction is needed use SignalManager.create_initial

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :returns: Signal object
        """
        from .models import Location, Status, CategoryAssignment, Reporter, Priority

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

        return signal

    def create_initial(self, signal_data, location_data, status_data, category_assignment_data,
                       reporter_data, priority_data=None):
        """Create a new `Signal` object with all related objects.

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :returns: Signal object
        """

        with transaction.atomic():
            signal = self._create_initial_no_transaction(
                signal_data=signal_data,
                location_data=location_data,
                status_data=status_data,
                category_assignment_data=category_assignment_data,
                reporter_data=reporter_data,
                priority_data=priority_data
            )

            transaction.on_commit(lambda: create_initial.send_robust(sender=self.__class__,
                                                                     signal_obj=signal))

        return signal

    def split(self, split_data, signal, user=None):
        """ Split the original signal into 2 or more (see settings SIGNAL_MAX_NUMBER_OF_CHILDREN)
            new signals

        :param split_data: deserialized data dict containing data for new signals
        :param signal: Signal object, the original Signal
        :return: Signal object, the original Signal
        """
        # See: https://docs.djangoproject.com/en/2.1/topics/db/queries/#copying-model-instances
        from .models import (Attachment, CategoryAssignment, Location, Priority, Reporter,
                             Signal, Status)
        from signals.apps.signals import workflow

        loop_counter = 0
        parent_signal = signal
        with transaction.atomic():
            for validated_data in split_data:
                loop_counter += 1

                # Create a new Signal, save it to get an ID in DB.
                child_signal = Signal.objects.create(**{
                    'text': validated_data['text'],
                    'incident_date_start': parent_signal.incident_date_start,
                    'parent': parent_signal,
                })

                # Set the relevant properties: location, status, reporter, priority, cate
                # Deal with reverse foreign keys to child signal (for history tracking):
                status = Status.objects.create(**{
                    '_signal': child_signal,
                    'state': workflow.GEMELD,
                    'text': None,
                    'user': None,  # i.e. SIA system
                })

                location_data = {'_signal': child_signal}
                location_data.update({
                    k: getattr(parent_signal.location, k) for k in [
                        'geometrie',
                        'stadsdeel',
                        'buurt_code',
                        'address',
                        'created_by',
                        'extra_properties',
                        'bag_validated'
                    ]
                })
                location = Location.objects.create(**location_data)

                reporter_data = {'_signal': child_signal}
                reporter_data.update({
                    k: getattr(parent_signal.reporter, k) for k in ['email', 'phone', 'remove_at']
                })
                reporter = Reporter.objects.create(**reporter_data)

                priority = None
                if parent_signal.priority:
                    priority_data = {'_signal': child_signal}
                    priority_data.update({
                        k: getattr(parent_signal.priority, k) for k in ['priority', 'created_by']
                    })
                    priority = Priority.objects.create(**priority_data)

                category = validated_data['category']['sub_category']
                category_assignment_data = {
                    '_signal': child_signal,
                    'category': category,
                }

                category_assignment = CategoryAssignment.objects.create(**category_assignment_data)

                # Deal with forward foreign keys from child signal
                child_signal.location = location
                child_signal.status = status
                child_signal.reporter = reporter
                child_signal.priority = priority
                child_signal.category_assignment = category_assignment
                child_signal.save()

                # Ensure each child signal creation sends a DjangoSignal.
                transaction.on_commit(lambda: create_child.send_robust(sender=self.__class__,
                                                                       signal_obj=child_signal))

                # Check if we need to copy the images of the parent
                if 'reuse_parent_image' in validated_data and validated_data['reuse_parent_image']:
                    parent_image_qs = parent_signal.attachments.filter(is_image=True)
                    if parent_image_qs.exists():
                        for parent_image in parent_image_qs.all():
                            # Copy the original file and rename it by pre-pending the name with
                            # split_{loop_counter}_{original_name}
                            child_image_name = 'split_{}_{}'.format(
                                loop_counter,
                                parent_image.file.name.split('/').pop()
                            )

                            attachment = Attachment()
                            attachment._signal = child_signal
                            try:
                                attachment.file.save(name=child_image_name,
                                                     content=parent_image.file)
                            except FileNotFoundError:
                                pass
                            else:
                                attachment.save()

            # Let's update the parent signal status to GESPLITST
            status, prev_status = self._update_status_no_transaction({
                'state': workflow.GESPLITST,
                'text': 'Deze melding is opgesplitst.',
                'created_by': user.email if user else None,
            }, signal=parent_signal)

            transaction.on_commit(lambda: update_status.send_robust(sender=self.__class__,
                                                                    signal_obj=parent_signal,
                                                                    status=status,
                                                                    prev_status=prev_status))

        return signal

    def add_image(self, image, signal):
        return self.add_attachment(image, signal)

    def add_attachment(self, file, signal):
        from .models import Attachment

        with transaction.atomic():
            attachment = Attachment()
            attachment._signal = signal
            attachment.file = file
            attachment.save()

            if attachment.is_image:
                add_image.send_robust(sender=self.__class__, signal_obj=signal)

            add_attachment.send_robust(sender=self.__class__, signal_obj=signal)

        return attachment

    def _update_location_no_transaction(self, data, signal):
        """Update (create new) `Location` object for given `Signal` object.
            If a transaction is needed use SignalManager.update_location

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Location object
        """
        from .models import Location

        prev_location = signal.location
        location = Location.objects.create(**data, _signal_id=signal.id)
        signal.location = location
        signal.save()

        return location, prev_location

    def update_location(self, data, signal):
        """Update (create new) `Location` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Location object
        """
        with transaction.atomic():
            location, prev_location = self._update_location_no_transaction(data, signal)
            transaction.on_commit(lambda: update_location.send_robust(sender=self.__class__,
                                                                      signal_obj=signal,
                                                                      location=location,
                                                                      prev_location=prev_location))

        return location

    def _update_status_no_transaction(self, data, signal):
        """Update (create new) `Status` object for given `Signal` object.
            If a transaction is needed use SignalManager.update_status

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Status object
        """
        from .models import Status

        status = Status(_signal=signal, **data)
        status.full_clean()
        status.save()

        prev_status = signal.status
        signal.status = status
        signal.save()

        return status, prev_status

    def update_status(self, data, signal):
        """Update (create new) `Status` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Status object
        """
        with transaction.atomic():
            status, prev_status = self._update_status_no_transaction(data=data, signal=signal)
            transaction.on_commit(lambda: update_status.send_robust(sender=self.__class__,
                                                                    signal_obj=signal,
                                                                    status=status,
                                                                    prev_status=prev_status))
        return status

    def _update_category_assignment_no_transaction(self, data, signal):
        """Update (create new) `CategoryAssignment` object for given `Signal` object.
            If a transaction is needed use SignalManager.update_category_assignment

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Category object
        """
        from .models import CategoryAssignment

        prev_category_assignment = signal.category_assignment
        category_assignment = CategoryAssignment.objects.create(**data, _signal_id=signal.id)
        signal.category_assignment = category_assignment
        signal.save()

        return category_assignment, prev_category_assignment

    def update_category_assignment(self, data, signal):
        """Update (create new) `CategoryAssignment` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Category object
        """

        if 'category' not in data:
            raise ValidationError('Category not found in data')
        elif signal.category_assignment is not None \
                and signal.category_assignment.category.id == data['category'].id:
            # New category is the same as the old category. Skip
            return

        with transaction.atomic():
            category_assignment, prev_category_assignment = \
                self._update_category_assignment_no_transaction(data, signal)
            transaction.on_commit(lambda: update_category_assignment.send_robust(
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

            transaction.on_commit(lambda: update_reporter.send_robust(sender=self.__class__,
                                                                      signal_obj=signal,
                                                                      reporter=reporter,
                                                                      prev_reporter=prev_reporter))

        return reporter

    def _update_priority_no_transaction(self, data, signal):
        """Update (create new) `Priority` object for given `Signal` object.
           If a transaction is needed use SignalManager.update_priority

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Priority object
        """
        from .models import Priority

        prev_priority = signal.priority

        priority = Priority.objects.create(**data, _signal_id=signal.id)
        signal.priority = priority
        signal.save()

        return priority, prev_priority

    def update_priority(self, data, signal):
        """Update (create new) `Priority` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Priority object
        """
        with transaction.atomic():
            priority, prev_priority = self._update_priority_no_transaction(data, signal)
            transaction.on_commit(lambda: update_priority.send_robust(sender=self.__class__,
                                                                      signal_obj=signal,
                                                                      priority=priority,
                                                                      prev_priority=prev_priority))

        return priority

    def _create_note_no_transaction(self, data, signal):
        """Create a new `Note` object for a given `Signal` object.
           If a transaction is needed use SignalManager.create_note

        :param data: deserialized data dict
        :returns: Note object
        """
        from .models import Note

        note = Note.objects.create(**data, _signal_id=signal.id)
        return note

    def create_note(self, data, signal):
        """Create a new `Note` object for a given `Signal` object.

        :param data: deserialized data dict
        :returns: Note object
        """

        # Added for completeness of the internal API, and firing of Django
        # signals upon creation of a Note.
        with transaction.atomic():
            note = self._create_note_no_transaction(data, signal)
            transaction.on_commit(lambda: create_note.send_robust(sender=self.__class__,
                                                                  signal_obj=signal,
                                                                  note=note))
            signal.save()

        return note

    def update_multiple(self, data, signal):
        """
        Perform one atomic update on multiple properties of `Signal` object.

        Note, this updates:
        - CategoryAssignment, Location, Priority, Note, Status
        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Updated Signal object
        """

        with transaction.atomic():
            to_send = []
            sender = self.__class__

            if 'location' in data:
                location, prev_location = self._update_location_no_transaction(data['location'], signal)  # noqa: E501
                to_send.append((update_location, {
                    'sender': sender,
                    'signal_obj': signal,
                    'location': location,
                    'prev_location': prev_location
                }))

            if 'status' in data:
                status, prev_status = self._update_status_no_transaction(data['status'], signal)
                to_send.append((update_status, {
                    'sender': sender,
                    'signal_obj': signal,
                    'status': status,
                    'prev_status': prev_status
                }))

            if 'category_assignment' in data:
                # Only update if category actually changes (TODO: remove when we
                # add consistency checks to API -- i.e. when we check that only
                # the latest version of a Signal can be mutated.)
                if 'category' not in data['category_assignment']:
                    raise ValidationError('Category not found in data')
                elif signal.category_assignment.category.id != data['category_assignment']['category'].id:  # noqa: E501
                    category_assignment, prev_category_assignment = \
                        self._update_category_assignment_no_transaction(
                            data['category_assignment'], signal)

                    to_send.append((update_category_assignment, {
                        'sender': sender,
                        'signal_obj': signal,
                        'category_assignment': category_assignment,
                        'prev_category_assignment': prev_category_assignment
                    }))

            if 'priority' in data:
                priority, prev_priority = \
                    self._update_priority_no_transaction(data['priority'], signal)
                to_send.append((update_priority, {
                    'sender': sender,
                    'signal_obj': signal,
                    'priority': priority,
                    'prev_priority': prev_priority
                }))

            if 'notes' in data:
                # The 0 index is there because we only allow one note to be
                # added per PATCH.
                note = self._create_note_no_transaction(data['notes'][0], signal)
                to_send.append((create_note, {
                    'sender': sender,
                    'signal_obj': signal,
                    'note': note
                }))

            # Send out all Django signals:
            transaction.on_commit(lambda: send_signals(to_send))

        signal.refresh_from_db()
        return signal
