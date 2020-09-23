import os

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

from signals.settings import DEFAULT_SIGNAL_AREA_TYPE

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
update_type = DjangoSignal(providing_args=['signal_obj', 'type', 'prev_type'])


def send_signals(to_send):
    """
    Helper function, sends properly instantiated Django Signals.

    :param to_send: list of tuples of django signal definition and keyword arguments
    """
    for django_signal, kwargs in to_send:
        django_signal.send_robust(**kwargs)


class SignalManager(models.Manager):

    def _create_initial_no_transaction(self, signal_data, location_data, status_data,
                                       category_assignment_data, reporter_data, priority_data=None, type_data=None):
        """Create a new `Signal` object with all related objects.
            If a transaction is needed use SignalManager.create_initial

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :param type_data: deserialized data dict (Default: None)
        :returns: Signal object
        """
        from .models import Location, Status, CategoryAssignment, Reporter, Priority, Type
        from .utils.location import _get_stadsdeel_code, _get_area

        signal = self.create(**signal_data)

        # Set default (empty dict) value for `priority_data` if None is given.
        priority_data = priority_data or {}

        # SIG-2513 Determine the stadsdeel
        default_stadsdeel = location_data['stadsdeel'] if 'stadsdeel' in location_data else None
        location_data['stadsdeel'] = _get_stadsdeel_code(location_data['geometrie'], default_stadsdeel)

        # set area_type and area_code if default area type is provided
        if DEFAULT_SIGNAL_AREA_TYPE:
            area = _get_area(location_data['geometrie'], DEFAULT_SIGNAL_AREA_TYPE)
            if area:
                location_data['area_type_code'] = DEFAULT_SIGNAL_AREA_TYPE
                location_data['area_code'] = area.code

        # Create dependent model instances with correct foreign keys to Signal
        location = Location.objects.create(**location_data, _signal_id=signal.pk)
        status = Status.objects.create(**status_data, _signal_id=signal.pk)
        category_assignment = CategoryAssignment.objects.create(**category_assignment_data,
                                                                _signal_id=signal.pk)
        reporter = Reporter.objects.create(**reporter_data, _signal_id=signal.pk)
        priority = Priority.objects.create(**priority_data, _signal_id=signal.pk)

        type_data = type_data or {}  # If type_data is None a Type is created with the default "SIGNAL" value
        Type.objects.create(**type_data, _signal_id=signal.pk)

        # Set Signal to dependent model instance foreign keys
        signal.location = location
        signal.status = status
        signal.category_assignment = category_assignment
        signal.reporter = reporter
        signal.priority = priority
        signal.save()

        return signal

    def create_initial(self, signal_data, location_data, status_data, category_assignment_data,
                       reporter_data, priority_data=None, type_data=None):
        """Create a new `Signal` object with all related objects.

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :param type_data: deserialized data dict (Default: None)
        :returns: Signal object
        """

        with transaction.atomic():
            signal = self._create_initial_no_transaction(
                signal_data=signal_data,
                location_data=location_data,
                status_data=status_data,
                category_assignment_data=category_assignment_data,
                reporter_data=reporter_data,
                priority_data=priority_data,
                type_data=type_data,
            )

            transaction.on_commit(lambda: create_initial.send_robust(sender=self.__class__,
                                                                     signal_obj=signal))

        return signal

    def split(self, split_data, signal, user=None):  # noqa: C901
        """ Split the original signal into 2 or more (see settings SIGNAL_MAX_NUMBER_OF_CHILDREN)
            new signals

        :param split_data: deserialized data dict containing data for new signals
        :param signal: Signal object, the original Signal
        :return: Signal object, the original Signal
        """
        # See: https://docs.djangoproject.com/en/2.1/topics/db/queries/#copying-model-instances
        from .models import (Attachment, CategoryAssignment, Location, Priority, Reporter,
                             Signal, Status, Type)
        from signals.apps.signals import workflow

        loop_counter = 0
        with transaction.atomic():
            parent_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)
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
                        'area_type_code',
                        'area_code',
                        'address',
                        'created_by',
                        'extra_properties',
                        'bag_validated'
                    ]
                })
                location = Location.objects.create(**location_data)

                reporter_data = {'_signal': child_signal}
                reporter_data.update({
                    k: getattr(parent_signal.reporter, k) for k in ['email', 'phone', 'email_anonymized', 'phone_anonymized', 'sharing_allowed']  # noqa
                })
                reporter = Reporter.objects.create(**reporter_data)

                priority = None
                if parent_signal.priority:
                    priority_data = {'_signal': child_signal}
                    priority_data.update({
                        k: getattr(parent_signal.priority, k) for k in ['priority', 'created_by']
                    })
                    priority = Priority.objects.create(**priority_data)

                if 'category_url' in validated_data['category']:
                    category = validated_data['category']['category_url']
                elif 'sub_category' in validated_data['category']:
                    # Only for backwards compatibility
                    category = validated_data['category']['sub_category']

                category_assignment_data = {
                    '_signal': child_signal,
                    'category': category,
                }

                category_assignment = CategoryAssignment.objects.create(**category_assignment_data)

                if 'type' in validated_data:
                    type_data = validated_data['type']  # Will create a type with the given name
                    type_data['created_by'] = None  # noqa We also set the other fields to None. Shouldn't this be "user if user else None"?
                elif parent_signal.type_assignment:
                    type_data = {
                        'name': parent_signal.type_assignment.name,   # noqa Will copy the type with name from the parent signal
                        'created_by': None  # noqa We also set the other fields to None. Shouldn't this be "user if user else None"?
                    }
                else:
                    type_data = {}  # Will create a default type with name "SIGNAL"

                # Creates the Type for the child signal
                Type.objects.create(**type_data, _signal_id=child_signal.pk)

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
            # Do not take lock, uploads are slow and the lock is not needed for
            # consistency of the history and the signal itself because there
            # is no foreign key from Signal to Attachment.
            # Fixes: SIG-2367 (second and third upload fail because database
            # is locked while the first upload is taking place).
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
        from .utils.location import _get_stadsdeel_code, _get_area

        # SIG-2513 Determine the stadsdeel
        default_stadsdeel = data['stadsdeel'] if 'stadsdeel' in data else None
        data['stadsdeel'] = _get_stadsdeel_code(data['geometrie'], default_stadsdeel)

        # set area_type and area_code if default area type is provided
        if DEFAULT_SIGNAL_AREA_TYPE:
            area = _get_area(data['geometrie'], DEFAULT_SIGNAL_AREA_TYPE)
            if area:
                data['area_type_code'] = DEFAULT_SIGNAL_AREA_TYPE
                data['area_code'] = area.code

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
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            location, prev_location = self._update_location_no_transaction(data, locked_signal)
            transaction.on_commit(lambda: update_location.send_robust(sender=self.__class__,
                                                                      signal_obj=locked_signal,
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
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            status, prev_status = self._update_status_no_transaction(data=data, signal=locked_signal)
            transaction.on_commit(lambda: update_status.send_robust(sender=self.__class__,
                                                                    signal_obj=locked_signal,
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

        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            category_assignment, prev_category_assignment = \
                self._update_category_assignment_no_transaction(data, locked_signal)
            transaction.on_commit(lambda: update_category_assignment.send_robust(
                sender=self.__class__,
                signal_obj=locked_signal,
                category_assignment=category_assignment,
                prev_category_assignment=prev_category_assignment))

        return category_assignment

    def update_reporter(self, data, signal):
        """Update (create new) `Reporter` object for given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Reporter object
        """
        from .models import Reporter, Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            prev_reporter = signal.reporter

            reporter = Reporter.objects.create(**data, _signal_id=locked_signal.id)
            signal.reporter = reporter
            signal.save()

            transaction.on_commit(lambda: update_reporter.send_robust(sender=self.__class__,
                                                                      signal_obj=locked_signal,
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
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            priority, prev_priority = self._update_priority_no_transaction(data, signal)
            transaction.on_commit(lambda: update_priority.send_robust(sender=self.__class__,
                                                                      signal_obj=locked_signal,
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
        from signals.apps.signals.models import Signal

        # Added for completeness of the internal API, and firing of Django
        # signals upon creation of a Note.
        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            note = self._create_note_no_transaction(data, locked_signal)
            transaction.on_commit(lambda: create_note.send_robust(sender=self.__class__,
                                                                  signal_obj=locked_signal,
                                                                  note=note))
            locked_signal.save()

        return note

    def update_multiple(self, data, signal):  # noqa: C901
        """
        Perform one atomic update on multiple properties of `Signal` object.

        Note, this updates:
        - CategoryAssignment, Location, Priority, Note, Status
        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Updated Signal object
        """
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal

            to_send = []
            sender = self.__class__

            if 'location' in data:
                location, prev_location = self._update_location_no_transaction(data['location'], locked_signal)  # noqa: E501
                to_send.append((update_location, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'location': location,
                    'prev_location': prev_location
                }))

            if 'status' in data:
                status, prev_status = self._update_status_no_transaction(data['status'], locked_signal)
                to_send.append((update_status, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'status': status,
                    'prev_status': prev_status
                }))

            if 'category_assignment' in data:
                # Only update if category actually changes (TODO: remove when we
                # add consistency checks to API -- i.e. when we check that only
                # the latest version of a Signal can be mutated.)
                if 'category' not in data['category_assignment']:
                    raise ValidationError('Category not found in data')
                elif locked_signal.category_assignment.category.id != data['category_assignment']['category'].id:  # noqa: E501
                    category_assignment, prev_category_assignment = \
                        self._update_category_assignment_no_transaction(
                            data['category_assignment'], locked_signal)

                    to_send.append((update_category_assignment, {
                        'sender': sender,
                        'signal_obj': locked_signal,
                        'category_assignment': category_assignment,
                        'prev_category_assignment': prev_category_assignment
                    }))

            if 'priority' in data:
                priority, prev_priority = \
                    self._update_priority_no_transaction(data['priority'], locked_signal)
                to_send.append((update_priority, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'priority': priority,
                    'prev_priority': prev_priority
                }))

            if 'notes' in data:
                # The 0 index is there because we only allow one note to be
                # added per PATCH.
                note = self._create_note_no_transaction(data['notes'][0], locked_signal)
                to_send.append((create_note, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'note': note
                }))

            if 'type' in data:
                previous_type = locked_signal.type_assignment
                signal_type = self._update_type_no_transaction(data['type'], locked_signal)
                to_send.append((update_type, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'type': signal_type,
                    'prev_type': previous_type
                }))

            if 'directing_departments_assignment' in data:
                previous_directing_departments = locked_signal.directing_departments_assignment
                directing_departments = self._update_directing_departments_no_transaction(
                    data['directing_departments_assignment'], locked_signal
                )
                to_send.append((update_type, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'directing_departments': directing_departments,
                    'prev_directing_departments': previous_directing_departments
                }))

            if 'signal_departments' in data:
                previous_signal_departments = locked_signal.signal_departments
                update_detail_data = data['signal_departments']
                signal_departments = self._update_signal_departments_list_no_transaction(
                    update_detail_data, locked_signal
                )
                to_send.append((update_type, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'signal_departments': signal_departments,
                    'prev_signal_departments': previous_signal_departments
                }))

            if 'assigned_user_id' in data:
                previous_user_assignment = locked_signal.assigned_user_id
                user_assignment = self._update_user_signal_no_transaction(
                    data, locked_signal
                )
                to_send.append((update_type, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'assigned_user_id': user_assignment,
                    'prev_assigned_user_id': previous_user_assignment
                }))

            # Send out all Django signals:
            transaction.on_commit(lambda: send_signals(to_send))

        locked_signal.refresh_from_db()
        return locked_signal

    def _update_type_no_transaction(self, data, signal):
        """Update (create new) `Type` object for given `Signal` object.
           If a transaction is needed use SignalManager.update_type

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Type object
        """
        from signals.apps.signals.models import Type

        signal_type = Type.objects.create(**data, _signal_id=signal.pk)
        return signal_type

    def update_type(self, data, signal):
        """Create a new `Type` object for a given `Signal` object.

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Type object
        """
        with transaction.atomic():
            previous_type = signal.type_assignment
            signal_type = self._update_type_no_transaction(data=data, signal=signal)

            transaction.on_commit(lambda: update_type.send_robust(sender=self.__class__, signal_obj=signal,
                                                                  type=signal_type, prev_type=previous_type))

        return signal_type

    def _update_user_signal_no_transaction(self, data, signal):
        from signals.apps.users.models import User, SignalUser

        if not hasattr(signal, 'user_assignment'):
            signal.user_assignment = SignalUser.objects.create(
                _signal=signal,
                user=User.objects.get(pk=data['assigned_user_id']),
                created_by=data['created_by'] if 'created_by' in data else None
            )
        else:
            signal.user_assignment.user = None
            if data['assigned_user_id']:
                signal.user_assignment.user = User.objects.get(pk=data['assigned_user_id'])
            signal.user_assignment.save()

        signal.save()
        return signal.user_assignment

    def _update_signal_departments_list_no_transaction(self, data, signal):
        from signals.apps.signals.models.signal_departments import SignalDepartments
        lst = []
        for relation in data:
            obj, _ = SignalDepartments.objects.get_or_create(
                _signal=signal,
                relation_type=relation['relation_type'],
            )
            obj.created_by = relation['created_by'] if 'created_by' in relation else None
            obj.departments.set([dept['id'] for dept in relation['departments']])
            obj.save()
            lst.append(obj)

        signal.signal_departments.set(lst)
        signal.save()
        return signal.signal_departments

    def _update_signal_departments_no_transaction(self, data, signal, relation_type):
        from signals.apps.signals.models.signal_departments import SignalDepartments

        relation, created = SignalDepartments.objects.get_or_create(
            _signal=signal,
            relation_type=relation_type,
        )
        if not created:
            relation.departments.clear()

        relation.created_by = data['created_by'] if 'created_by' in data else None
        for department_data in data['departments']:
            relation.departments.add(department_data['id'])

        if created:
            signal.signal_departments.add(relation)
            signal.save()
        else:
            relation.save()
        return relation

    def _update_directing_departments_no_transaction(self, data, signal):
        from signals.apps.signals.models.signal_departments import SignalDepartments
        return self._update_signal_departments_no_transaction(data, signal, SignalDepartments.REL_DIRECTING)

    def _update_routing_departments_no_transaction(self, data, signal):
        from signals.apps.signals.models.signal_departments import SignalDepartments
        return self._update_signal_departments_no_transaction(data, signal, SignalDepartments.REL_ROUTING)

    def update_signal_departments(self, data, signal, relation_type):
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal
            directing_departments = self._update_signal_departments_no_transaction(
                data=data,
                signal=locked_signal,
                relation_type=relation_type
            )

        return directing_departments

    # REMOVE? seems unused
    def update_directing_departments(self, data, signal):
        from signals.apps.signals.models.signal_departments import SignalDepartments
        return self.update_signal_departments(data, signal, SignalDepartments.REL_DIRECTING)

    def update_routing_departments(self, data, signal):
        from signals.apps.signals.models.signal_departments import SignalDepartments
        return self.update_signal_departments(data, signal, SignalDepartments.REL_ROUTING)

    def _copy_attachment_no_transaction(self, source_attachment, signal):
        from signals.apps.signals.models import Attachment

        target_attachment = Attachment()
        target_attachment._signal = signal

        try:
            _, file_name = os.path.split(source_attachment.file.name)
            target_attachment.file.save(name=f'signal_{signal.pk}_{file_name}', content=source_attachment.file)
        except FileNotFoundError:
            pass
        else:
            target_attachment.save()
            return target_attachment

    def copy_attachments(self, data, signal):
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            attachments = []
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal
            for attachment in data:
                attachments.append(self._copy_attachment_no_transaction(attachment, locked_signal))
        return attachments
