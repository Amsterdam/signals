# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import os

from datapunt_api.rest import DisplayField, HALSerializer
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.fields import (
    PrivateSignalAttachmentRelatedField,
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    PublicSignalLinksField,
    SignalExtraPropertiesField
)
from signals.apps.api.generics.permissions import (
    SIAPermissions,
    SignalChangeCategoryPermission,
    SignalChangeStatusPermission,
    SignalCreateInitialPermission,
    SignalCreateNotePermission
)
from signals.apps.api.serializers.nested import (
    _NestedCategoryModelSerializer,
    _NestedDepartmentModelSerializer,
    _NestedLocationModelSerializer,
    _NestedNoteModelSerializer,
    _NestedPriorityModelSerializer,
    _NestedPublicStatusModelSerializer,
    _NestedReporterModelSerializer,
    _NestedStatusModelSerializer,
    _NestedTypeModelSerializer
)
from signals.apps.api.validation.address.mixin import AddressValidationMixin
from signals.apps.api.validation.mixin import SignalValidationMixin
from signals.apps.api.validators.extra_properties import ExtraPropertiesValidator
from signals.apps.api.validators.source import (
    PrivateSignalSourceValidator,
    PublicSignalSourceValidator
)
from signals.apps.questionnaires.models import Session
from signals.apps.signals import workflow
from signals.apps.signals.models import Attachment, Priority, Signal


class _SignalListSerializer(serializers.ListSerializer):
    """
    A custom "list_serializer_class" that is set on the PrivateSignalSerializerList.
    The PrivateSignalSerializerList is the only serializer that allows the creation of Signals.
    This class provides custom validation for the creation of Signals OR child Signals in bulk.
    """
    def validate(self, attrs):
        """
        Validate the data given.

        The API allows the bulk creation of Signals if:

         * All Signals given do not have a parent

         * All Signals given need to be children of the same Signal
         ** The given Signals + the already existing child Signals do not exceed X

         * A maximum of X Signals can be sent to create in bulk (defined in the setting SIGNAL_MAX_NUMBER_OF_CHILDREN)

        :param attrs:
        :return attrs:
        """
        if len(attrs) > settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            raise ValidationError(
                f'Only a maximum of {settings.SIGNAL_MAX_NUMBER_OF_CHILDREN} Signals can be created in bulk'
            )

        # Get all parent id's from the attrs
        parent_ids = [signal_data['parent'].pk for signal_data in attrs if 'parent' in signal_data]

        if len(attrs) > 0 and len(parent_ids) == 0:
            # We are only creating normal Signals so we can continue
            return attrs

        if len(attrs) != len(parent_ids):
            # Check if the given data is not mixing the creation of Signals and Child Signals
            raise ValidationError('Only Signals OR Child Signals (of the same parent) can be created in bulk')

        # Additional checks for the creation of child Signals
        if len(set(parent_ids)) > 1:
            raise ValidationError('All Parent ID\'s must be the same Signal')

        # We know that all provided parent's are the same so just get the parent from the first child
        signal = attrs[0]['parent']
        if signal.is_child:
            raise ValidationError('The given parent Signal is itself a child, therefore it cannot have children')

        number_of_children_in_db = signal.children.count()
        if number_of_children_in_db >= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            raise ValidationError(
                f'Maximum number of {settings.SIGNAL_MAX_NUMBER_OF_CHILDREN} child Signals reached for parent Signal'
            )

        if number_of_children_in_db + len(attrs) > settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            raise ValidationError(
                f'Cannot create the given child signals because this will exceed the maximum of children allowed on a '
                f'Signal. Which is set to {settings.SIGNAL_MAX_NUMBER_OF_CHILDREN} child Signals per parent Signal'
            )

        return attrs


class PrivateSignalSerializerDetail(HALSerializer, AddressValidationMixin):
    """
    This serializer is used for the detail endpoint and when updating the instance
    """
    serializer_url_field = PrivateSignalLinksFieldWithArchives
    _display = DisplayField()

    location = _NestedLocationModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,)
    )

    status = _NestedStatusModelSerializer(
        required=False,
        permission_classes=(SignalChangeStatusPermission,)
    )

    category = _NestedCategoryModelSerializer(
        source='category_assignment',
        required=False,
        permission_classes=(SignalChangeCategoryPermission,)
    )

    reporter = _NestedReporterModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,)
    )

    priority = _NestedPriorityModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,)
    )

    notes = _NestedNoteModelSerializer(
        many=True,
        required=False,
        permission_classes=(SignalCreateNotePermission,)
    )

    type = _NestedTypeModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,),
        source='type_assignment',
    )

    directing_departments = _NestedDepartmentModelSerializer(
        source='directing_departments_assignment.departments',
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    routing_departments = _NestedDepartmentModelSerializer(
        source='routing_assignment.departments',
        many=True,
        required=False,
        allow_null=True,
        permission_classes=(SIAPermissions,),
    )

    has_attachments = serializers.SerializerMethodField()

    assigned_user_email = serializers.EmailField(source='user_assignment.user.email', required=False, allow_null=True)

    extra_properties = SignalExtraPropertiesField(
        required=False,
        validators=[
            ExtraPropertiesValidator(filename=os.path.join(
                os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json')
            )
        ]
    )

    attachments = PrivateSignalAttachmentRelatedField(view_name='private-signals-attachments-detail', many=True,
                                                      required=False, read_only=True)

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'category',
            'id',
            'has_attachments',
            'location',
            'status',
            'reporter',
            'priority',
            'notes',
            'type',
            'source',
            'text',
            'text_extra',
            'extra_properties',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'directing_departments',
            'routing_departments',
            'attachments',
            'assigned_user_email',
        )
        read_only_fields = (
            'id',
            'has_attachments',
        )

    def get_has_attachments(self, obj):
        return obj.attachments.exists()

    def update(self, instance, validated_data): # noqa
        """
        Perform update on nested models.

        Note:
        - Reporter cannot be updated via the API.
        - Atomic update (all fail/succeed), django signals on full success (see
          underlying update_multiple method of actions SignalManager).
        """
        if not instance.is_parent and validated_data.get('directing_departments_assignment') is not None:
            raise serializers.ValidationError('Directing departments can only be set on a parent Signal')

        user_email = self.context['request'].user.email

        for _property in ['location', 'status', 'category_assignment', 'priority']:
            if _property in validated_data:
                data = validated_data[_property]
                data['created_by'] = user_email

        if 'type_assignment' in validated_data:
            type_data = validated_data.pop('type_assignment')
            type_data['created_by'] = user_email
            validated_data['type'] = type_data

        if 'notes' in validated_data and validated_data['notes']:
            note_data = validated_data['notes'][0]
            note_data['created_by'] = user_email

        if 'directing_departments_assignment' in validated_data and validated_data['directing_departments_assignment']:
            validated_data['directing_departments_assignment']['created_by'] = user_email

        if 'routing_assignment' in validated_data and validated_data['routing_assignment']:
            validated_data['routing_assignment']['created_by'] = user_email

        if 'user_assignment' in validated_data and validated_data['user_assignment']:
            validated_data['created_by'] = user_email

        signal = Signal.actions.update_multiple(validated_data, instance)
        return signal


class PrivateSignalSerializerList(SignalValidationMixin, HALSerializer):
    """
    This serializer is used for the list endpoint and when creating a new instance
    """
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

    signal_id = serializers.UUIDField(source='uuid', required=False, read_only=True)

    location = _NestedLocationModelSerializer(
        permission_classes=(SIAPermissions,)
    )

    status = _NestedStatusModelSerializer(
        required=False,
        permission_classes=(SignalCreateInitialPermission,)
    )

    category = _NestedCategoryModelSerializer(
        source='category_assignment',
        permission_classes=(SignalCreateInitialPermission,)
    )

    reporter = _NestedReporterModelSerializer(
        permission_classes=(SIAPermissions,)
    )

    priority = _NestedPriorityModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,)
    )

    notes = _NestedNoteModelSerializer(
        many=True,
        required=False,
        permission_classes=(SignalCreateInitialPermission,)
    )

    type = _NestedTypeModelSerializer(
        required=False,
        permission_classes=(SIAPermissions,),
        source='type_assignment',
    )

    directing_departments = _NestedDepartmentModelSerializer(
        source='directing_departments_assignment.departments',
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    routing_departments = _NestedDepartmentModelSerializer(
        source='routing_assignment.departments',
        many=True,
        required=False,
        allow_null=True,
        permission_classes=(SIAPermissions,),
    )

    has_attachments = serializers.SerializerMethodField()

    assigned_user_email = serializers.EmailField(source='user_assignment.user.email', required=False, allow_null=True)

    extra_properties = SignalExtraPropertiesField(
        required=False,
        allow_null=True,
        validators=[
            ExtraPropertiesValidator(
                filename=os.path.join(
                    os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json')
            )
        ]
    )

    parent = serializers.PrimaryKeyRelatedField(
        required=False,
        read_only=False,
        write_only=True,
        queryset=Signal.objects.all()
    )
    has_parent = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()

    attachments = PrivateSignalAttachmentRelatedField(view_name='private-signals-attachments-detail', many=True,
                                                      required=False, read_only=False, write_only=True,
                                                      queryset=Attachment.objects.all())

    # The Session containing the given answers of a Questionnaire
    session = serializers.UUIDField(default=None, write_only=True, required=False)

    class Meta:
        model = Signal
        list_serializer_class = _SignalListSerializer
        fields = (
            '_links',
            '_display',
            'id',
            'signal_id',
            'source',
            'text',
            'text_extra',
            'status',
            'location',
            'category',
            'reporter',
            'priority',
            'type',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'has_attachments',
            'extra_properties',
            'notes',
            'directing_departments',
            'routing_departments',
            'attachments',
            'parent',
            'has_parent',
            'has_children',
            'assigned_user_email',
            'session'
        )
        read_only_fields = (
            'created_at',
            'updated_at',
            'has_attachments',
            'has_parent',
            'has_children',
        )
        extra_kwargs = {
            'source': {'validators': [PrivateSignalSourceValidator()]},
        }

    def get_has_attachments(self, obj):
        return obj.attachments.exists()

    def get_has_parent(self, obj):
        return obj.parent_id is not None  # True is a parent_id is set, False if not

    def get_has_children(self, obj):
        return obj.children.exists()

    def validate(self, attrs):  # noqa C901
        errors = {}
        if attrs.get('directing_departments_assignment') is not None:
            errors.update(
                {'directing_departments_assignment': ['Directing departments cannot be set on initial creation']}
            )

        if attrs.get('routing_assignment') is not None:
            errors.update(
                {'routing_assignment': ['Signal departments relation cannot be set on initial creation']}
            )

        if attrs.get('status') is not None:
            errors.update(
                {'status': ['Status cannot be set on initial creation']}
            )

        attachments = attrs.get('attachments')
        parent = attrs.get('parent')
        if attachments and parent is None:
            errors.update({'attachments': ['Attachments can only be copied when creating a child Signal']})

        if attachments and parent:
            attachments_belong_to_parent = all([parent.pk == attachment._signal_id for attachment in attachments])
            if not attachments_belong_to_parent:
                errors.update({'attachments': ['Attachments can only be copied from the parent Signal']})

        if 'session' in attrs and attrs['session']:
            """
            If a Session UUID is given the following checks must be valid before it can be connected to the Signal that
            is going to be created created.

                - The Session with given UUID must exists
                - The Session cannot be connected to a Signal
                - The Session cannot be expired
                - The Session must be frozen
            """
            try:
                session = Session.objects.get(uuid=attrs['session'])
            except Session.DoesNotExist as e:
                errors.update({'session': [f'{e}']})
            else:
                if session._signal_id:
                    errors.update({'session': ['Session already used']})
                elif not session.frozen and not session.is_expired:
                    errors.update({'session': ['Session not frozen']})
                elif session.too_late:
                    errors.update({'session': ['Session expired']})
                else:
                    attrs['session'] = session

        # SIG-4382 additional check on the extra_properties if the category is lantaarpaal-straatverlichting
        if attrs.get('category_assignment').get('category').slug == 'lantaarnpaal-straatverlichting':
            validator = ExtraPropertiesValidator(filename=os.path.join(os.path.dirname(__file__), '..', 'json_schema',
                                                                       'extra_properties_streetlights.json'))
            try:
                validator(attrs.get('extra_properties'))
            except ValidationError:
                errors.update({'extra_properties': [
                    'Extra properties not valid for category "lantaarnpaal-straatverlichting"'
                ]})

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs=attrs)

    def create(self, validated_data):
        # Set default status
        logged_in_user = self.context['request'].user
        INITIAL_STATUS = {
            'state': workflow.GEMELD,  # see models.py is already default
            'text': None,
            'user': logged_in_user.email,
        }

        # We require location and reporter to be set and to be valid.
        reporter_data = validated_data.pop('reporter')

        location_data = validated_data.pop('location')
        location_data['created_by'] = logged_in_user.email

        category_assignment_data = validated_data.pop('category_assignment')
        category_assignment_data['created_by'] = logged_in_user.email

        # We will use the priority and signal type on the incoming message if present.
        priority_data = validated_data.pop('priority', {
            'priority': Priority.PRIORITY_NORMAL
        })
        priority_data['created_by'] = logged_in_user.email
        type_data = validated_data.pop('type_assignment', {})
        type_data['created_by'] = logged_in_user.email

        attachments = validated_data.pop('attachments') if 'attachments' in validated_data else None
        session = validated_data.pop('session')

        signal = Signal.actions.create_initial(
            validated_data,
            location_data,
            INITIAL_STATUS,
            category_assignment_data,
            reporter_data,
            priority_data,
            type_data,
            session=session,
        )

        if attachments:
            Signal.actions.copy_attachments(data=attachments, signal=signal)

        signal.refresh_from_db()
        return signal


class PublicSignalSerializerDetail(HALSerializer):
    status = _NestedPublicStatusModelSerializer(required=False)
    serializer_url_field = PublicSignalLinksField
    _display = serializers.SerializerMethodField(method_name='get__display')
    signal_id = serializers.UUIDField(source='uuid')

    class Meta:
        model = Signal
        fields = (
            '_display',
            'id',
            'signal_id',
            'status',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
        )

    def get__display(self, obj):
        return obj.sia_id


class PublicSignalCreateSerializer(SignalValidationMixin, serializers.ModelSerializer):
    """
    This serializer allows anonymous users to report `signals.Signals`.

    Note: this is only used in the creation of new Signal instances, not to
    create the response body after a succesfull POST.
    """
    source = serializers.CharField(default='online', validators=[PublicSignalSourceValidator()])
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    category = _NestedCategoryModelSerializer(source='category_assignment')
    incident_date_start = serializers.DateTimeField()
    extra_properties = SignalExtraPropertiesField(
        required=False,
        allow_null=True,
        validators=[
            ExtraPropertiesValidator(
                filename=os.path.join(
                    os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json'
                )
            )
        ]
    )

    # The Session containing the given answers of a Questionnaire
    session = serializers.UUIDField(default=None, write_only=True, required=False)

    class Meta(object):
        model = Signal
        fields = (
            'source',
            'text',
            'text_extra',
            'location',
            'category',
            'reporter',
            'incident_date_start',
            'incident_date_end',
            'extra_properties',
            'session',
        )

    def validate(self, data):  # noqa: C901
        """Make sure any extra data is rejected"""
        if hasattr(self, 'initial_data'):
            present_keys = set(self.initial_data)
            allowed_keys = set(self.fields)

            if present_keys - allowed_keys:
                raise ValidationError('Extra properties present: {}'.format(
                    ', '.join(present_keys - allowed_keys)
                ))

        errors = {}
        if 'session' in data and data['session']:
            """
            If a Session UUID is given the following checks must be valid before it can be connected to the Signal that
            is going to be created created.

                - The Session with given UUID must exists
                - The Session cannot be connected to a Signal
                - The Session cannot be expired
                - The Session must be frozen
            """
            try:
                session = Session.objects.get(uuid=data['session'])
            except Session.DoesNotExist as e:
                errors.update({'session': [f'{e}']})
            else:
                if session._signal_id:
                    errors.update({'session': ['Session already used']})
                elif not session.frozen and not session.is_expired:
                    errors.update({'session': ['Session not frozen']})
                elif session.too_late:
                    errors.update({'session': ['Session expired']})
                else:
                    data['session'] = session

        # SIG-4382 additional check on the extra_properties if the category is lantaarpaal-straatverlichting
        if data.get('category_assignment').get('category').slug == 'lantaarnpaal-straatverlichting':
            validator = ExtraPropertiesValidator(
                filename=os.path.join(os.path.dirname(__file__), '..', 'json_schema',
                                      'extra_properties_streetlights.json'))
            try:
                validator(data.get('extra_properties'))
            except ValidationError:
                errors.update({'extra_properties': [
                    'Extra properties not valid for category "lantaarnpaal-straatverlichting"'
                ]})

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(data)

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        category_assignment_data = validated_data.pop('category_assignment')
        session = validated_data.pop('session')

        return Signal.actions.create_initial(
            validated_data,
            location_data,
            {'state': workflow.GEMELD},
            category_assignment_data,
            reporter_data,
            priority_data=None,
            type_data=None,
            session=session,
        )


class SignalIdListSerializer(HALSerializer):
    class Meta:
        model = Signal
        fields = (
            'id',
        )


class AbridgedChildSignalSerializer(HALSerializer):
    serializer_url_field = PrivateSignalLinksField

    status = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    can_view_signal = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = (
            '_links',
            'id',
            'status',
            'category',
            'updated_at',
            'can_view_signal'
        )

    def get_status(self, obj):
        return {
            'state': obj.status.state,
            'state_display': obj.status.get_state_display(),
        }

    def get_category(self, obj):
        departments = ', '.join(
            obj.category_assignment.category.departments.filter(
                categorydepartment__is_responsible=True
            ).values_list('code', flat=True)
        )
        return {
            'sub': obj.category_assignment.category.name,
            'sub_slug': obj.category_assignment.category.slug,
            'departments': departments,
            'main': obj.category_assignment.category.parent.name,
            'main_slug': obj.category_assignment.category.parent.slug,
        }

    def get_can_view_signal(self, obj):
        return Signal.objects.filter(pk=obj.pk).filter_for_user(self.context['request'].user).exists()
