# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam, Delta10 B.V.
import os

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

from signals.settings import DEFAULT_SIGNAL_AREA_TYPE

# Declaring custom Django signals for our `SignalManager`.

create_initial = DjangoSignal()
create_child = DjangoSignal()
add_attachment = DjangoSignal()
update_location = DjangoSignal()
update_status = DjangoSignal()
update_category_assignment = DjangoSignal()
update_reporter = DjangoSignal()
update_priority = DjangoSignal()
create_note = DjangoSignal()
update_type = DjangoSignal()
update_user_assignment = DjangoSignal()
update_signal_departments = DjangoSignal()


def send_signals(to_send):
    """
    Helper function, sends properly instantiated Django Signals.

    :param to_send: list of tuples of django signal definition and keyword arguments
    """
    for django_signal, kwargs in to_send:
        django_signal.send_robust(**kwargs)


class SignalManager(models.Manager):

    def _create_initial_no_transaction(  # noqa: C901
            self, signal_data, location_data, status_data, category_assignment_data, reporter_data, priority_data=None,
            type_data=None, session=None):
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
        from .models import CategoryAssignment, Location, Priority, Reporter, Status, Type
        from .utils.location import _get_area, _get_stadsdeel_code

        if session:
            from signals.apps.questionnaires.services import SessionService
            session_service = SessionService(session)
            session_extra_properties = session_service.get_extra_properties()
            if 'extra_properties' in signal_data:
                signal_data['extra_properties'] = signal_data['extra_properties'] + session_extra_properties
            else:
                signal_data.update({'extra_properties': session_extra_properties})

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
                location_data['area_name'] = area.name

        # Create dependent model instances with correct foreign keys to Signal
        location = Location.objects.create(**location_data, _signal_id=signal.pk)
        status = Status.objects.create(**status_data, _signal_id=signal.pk)
        category_assignment = CategoryAssignment.objects.create(**category_assignment_data, _signal_id=signal.pk)

        # Original reporters should be transitioned to the approved state immediately.
        reporter = Reporter.objects.create(**reporter_data, _signal_id=signal.pk)
        reporter.approve()
        reporter.save()

        priority = Priority.objects.create(**priority_data, _signal_id=signal.pk)

        type_data = type_data or {}  # If type_data is None a Type is created with the default "SIGNAL" value
        signal_type = Type.objects.create(**type_data, _signal_id=signal.pk)

        # Set Signal to dependent model instance foreign keys
        signal.location = location
        signal.status = status
        signal.category_assignment = category_assignment
        signal.reporter = reporter
        signal.priority = priority
        signal.type_assignment = signal_type
        signal.save()

        if session:
            session._signal = signal
            session.save()

        return signal

    def create_initial(self, signal_data, location_data, status_data, category_assignment_data,
                       reporter_data, priority_data=None, type_data=None, session=None):
        """Create a new `Signal` object with all related objects.

        :param signal_data: deserialized data dict
        :param location_data: deserialized data dict
        :param status_data: deserialized data dict
        :param category_assignment_data: deserialized data dict
        :param reporter_data: deserialized data dict
        :param priority_data: deserialized data dict (Default: None)
        :param type_data: deserialized data dict (Default: None)
        :param session: Session object (Default: None)
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
                session=session,
            )

            transaction.on_commit(lambda: create_initial.send_robust(sender=self.__class__,
                                                                     signal_obj=signal))

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

            # SIG-2213 use transaction.on_commit to send relevant Django signals
            transaction.on_commit(lambda: add_attachment.send_robust(
                sender=self.__class__, signal_obj=signal, attachment=attachment))

        return attachment

    def _update_location_no_transaction(self, data, signal):
        """Update (create new) `Location` object for given `Signal` object.
            If a transaction is needed use SignalManager.update_location

        :param data: deserialized data dict
        :param signal: Signal object
        :returns: Location object
        """
        from .models import Location
        from .utils.location import _get_area, _get_stadsdeel_code

        # SIG-2513 Determine the stadsdeel
        default_stadsdeel = data['stadsdeel'] if 'stadsdeel' in data else None
        data['stadsdeel'] = _get_stadsdeel_code(data['geometrie'], default_stadsdeel)

        # set area_type and area_code if default area type is provided
        if DEFAULT_SIGNAL_AREA_TYPE:
            area = _get_area(data['geometrie'], DEFAULT_SIGNAL_AREA_TYPE)
            if area:
                data['area_type_code'] = DEFAULT_SIGNAL_AREA_TYPE
                data['area_code'] = area.code
                data['area_name'] = area.name

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

        # Ensures that the 'updated_at' timestamp accurately reflects the most
        # recent activity related to a Signal, without altering any other
        # existing data
        signal.save(update_fields=['updated_at'])

        return note

    def create_note(self, data: dict, signal):
        """Create a new `Note` object for a given `Signal` object."""
        # Added for completeness of the internal API, and firing of Django
        # signals upon creation of a Note.

        with transaction.atomic():
            note = self._create_note_no_transaction(data, signal)

            transaction.on_commit(lambda: create_note.send_robust(sender=self.__class__,
                                                                  signal_obj=signal,
                                                                  note=note))

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
        from signals.apps.signals.models.signal_departments import SignalDepartments

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

                    self._clear_routing_and_assigned_user_no_transaction(locked_signal)
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
                signal_departments = self._update_signal_departments_no_transaction(
                    data['directing_departments_assignment'],
                    locked_signal,
                    SignalDepartments.REL_DIRECTING
                )
                to_send.append((update_signal_departments, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'signal_departments': signal_departments
                }))

            if 'routing_assignment' in data:
                previous_signal_departments = locked_signal.routing_assignment
                update_detail_data = data['routing_assignment']
                signal_departments = self._update_signal_departments_no_transaction(
                    update_detail_data,
                    locked_signal,
                    SignalDepartments.REL_ROUTING
                )
                to_send.append((update_signal_departments, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'signal_departments': signal_departments,
                    'prev_signal_departments': previous_signal_departments
                }))

            if 'user_assignment' in data:
                previous_user_assignment = locked_signal.user_assignment
                user_assignment = self._update_user_signal_no_transaction(
                    data, locked_signal
                )
                to_send.append((update_user_assignment, {
                    'sender': sender,
                    'signal_obj': locked_signal,
                    'user_assignment': user_assignment,
                    'prev_user_assignment': previous_user_assignment
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
        signal.type_assignment = signal_type
        signal.save()

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
        from signals.apps.signals.models.signal_user import SignalUser
        from signals.apps.users.models import User

        created_by = data['user_assignment']['created_by'] if 'created_by' in data['user_assignment'] else None
        assigned_user_email = data['user_assignment']['user']['email'] if data['user_assignment'] else None
        try:
            assigned_user = User.objects.get(email=assigned_user_email) if assigned_user_email else None
        except User.DoesNotExist:
            raise ValidationError('Could not set user assignment, user does not exist')

        signal.user_assignment = SignalUser.objects.create(
            _signal=signal,
            user=assigned_user,
            created_by=created_by
        )
        signal.save()

        return signal.user_assignment

    def _update_signal_departments_no_transaction(self, data, signal, relation_type):
        """Update (create new) SignalDepartments relation.

        Note: This is used for Directing Departments and Routing Departments.
        """
        from signals.apps.signals.models.signal_departments import SignalDepartments

        relation = SignalDepartments.objects.create(
            _signal=signal,
            relation_type=relation_type,
            created_by=data['created_by'] if 'created_by' in data else None
        )

        # Check if different Routing department(s) is/(are) already set, reset
        # assigned user as well.
        if signal.user_assignment and relation_type == SignalDepartments.REL_ROUTING:
            if signal.routing_assignment and signal.routing_assignment.departments.exclude(
                id__in=[dept.id for dept in relation.departments.all()]
            ).exists():
                signal.user_assignment = None  # TODO: consider adding log-entry here

        for department_data in data['departments']:
            relation.departments.add(department_data['id'])

        if relation_type == SignalDepartments.REL_DIRECTING:
            signal.directing_departments_assignment = relation
        elif relation_type == SignalDepartments.REL_ROUTING:
            signal.routing_assignment = relation
        else:
            raise ValidationError(f'Signal - department relation {relation_type} is not supported')
        signal.save()

        return relation

    def _clear_routing_and_assigned_user_no_transaction(self, signal):
        if signal.user_assignment:
            signal.user_assignment = None
        if signal.routing_assignment:
            signal.routing_assignment = None
        signal.save()
        return signal

    def update_routing_departments(self, data, signal):
        from signals.apps.signals.models import Signal
        from signals.apps.signals.models.signal_departments import SignalDepartments

        with transaction.atomic():
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal
            departments = self._update_signal_departments_no_transaction(
                data=data,
                signal=locked_signal,
                relation_type=SignalDepartments.REL_ROUTING
            )
            transaction.on_commit(lambda: update_signal_departments.send_robust(sender=self.__class__,
                                                                                signal_obj=signal,
                                                                                signal_departments=departments))

        return departments

    def _copy_attachment_no_transaction(self, source_attachment, signal, created_by):
        from signals.apps.signals.models import Attachment

        target_attachment = Attachment()
        target_attachment._signal = signal
        target_attachment.created_by = created_by

        try:
            _, file_name = os.path.split(source_attachment.file.name)
            target_attachment.file.save(name=f'signal_{signal.pk}_{file_name}', content=source_attachment.file)
        except FileNotFoundError:
            pass
        else:
            target_attachment.save()
            return target_attachment

    def copy_attachments(self, data, signal, created_by):
        from signals.apps.signals.models import Signal

        with transaction.atomic():
            to_send = []
            sender = self.__class__

            attachments = []
            locked_signal = Signal.objects.select_for_update(nowait=True).get(pk=signal.pk)  # Lock the Signal
            for attachment in data:
                attachments.append(self._copy_attachment_no_transaction(attachment, locked_signal, created_by))
                to_send.append((add_attachment, {'sender': sender, 'signal_obj': signal, 'attachment': attachment}))

            transaction.on_commit(lambda: send_signals(to_send))  # SIG-2213

        return attachments
