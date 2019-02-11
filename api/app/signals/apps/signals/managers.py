import copy

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


class SignalManager(models.Manager):

    def _create_initial_no_transaction(self, signal_data, location_data, status_data,
                                       category_assignment_data, reporter_data, priority_data=None):
        """Create a new `Signal` object with all related objects.
            If a transaction is needed use create_initial

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

            transaction.on_commit(lambda: create_initial.send(sender=self.__class__,
                                                              signal_obj=signal))

        return signal

    def split(self, split_data, signal):
        """ Split the original signal into 2 or more (see settings SIGNAL_MAX_NUMBER_OF_CHILDREN)
            new signals

        :param split_data: deserialized data dict containing data for new signals
        :param signal: Signal object, the original Signal
        :return: Signal object, the original Signal
        """
        from .models import Status
        from signals.apps.signals import workflow

        with transaction.atomic():
            # The initial status for all new splitted signals
            initial_status = {'state': workflow.GEMELD, 'text': None, 'user': signal.status.user, }

            for validated_data in split_data:
                split_signal = copy.deepcopy(signal)

                create_objs = {'location': None,  # We are copying this from the parent
                               'reporter': None,  # We are copying this from the parent
                               'priority': None,  # We are copying this from the parent
                               'category_assignment': None}  # We are copying this from the parent
                for attr in create_objs.keys():
                    if hasattr(split_signal, attr):
                        create_objs[attr] = getattr(split_signal, attr)
                        setattr(create_objs[attr], 'pk', None)
                        setattr(create_objs[attr], '_signal', None)
                        setattr(split_signal, attr, None)

                # Save the cloned signal to the database
                split_signal.status = None
                split_signal.pk = None
                split_signal.save()

                # Also add a the status GEMELD
                create_objs.update({'status': Status(**initial_status)})

                for key, obj in create_objs.items():
                    obj._signal_id = split_signal.pk
                    obj.save()

                # Set data from the serializer
                split_signal.text = validated_data['text']

                # Link to parent signal
                split_signal.parent_id = signal.pk

                # Store the signal with all the cloned data to the database
                split_signal.save()

            # Let's update the parent signal status to GESPLITST
            status, prev_status = self._update_status_no_transaction(
                {'state': workflow.GESPLITST, 'text': 'Signal opgesplitst.', },
                signal=signal
            )

            transaction.on_commit(lambda: update_status.send(sender=self.__class__,
                                                             signal_obj=signal,
                                                             status=status,
                                                             prev_status=prev_status))

        return signal

    def add_image(self, image, signal):
        with transaction.atomic():
            signal.image = image
            signal.save()

            add_image.send(sender=self.__class__, signal_obj=signal)

        return image

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

    def _update_status_no_transaction(self, data, signal):
        """ Update (create new) `Status` object for given `Signal` object.
            If a transaction is needed use update status

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
        """ Add a transaction to the _update_status_no_transaction

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Status object
        """
        with transaction.atomic():
            status, prev_status = self._update_status_no_transaction(data=data, signal=signal)
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
            signal.save()

        return note
