import os

from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.generics.permissions.base import (
    SignalChangeCategoryPermission,
    SignalChangeStatusPermission,
    SignalCreateInitialPermission,
    SignalCreateNotePermission
)
from signals.apps.api.generics.validators import SignalSourceValidator
from signals.apps.api.v1.fields import (
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    PublicSignalLinksField
)
from signals.apps.api.v1.fields.extra_properties import SignalExtraPropertiesField
from signals.apps.api.v1.serializers.nested import (
    _NestedAttachmentModelSerializer,
    _NestedCategoryModelSerializer,
    _NestedLocationModelSerializer,
    _NestedNoteModelSerializer,
    _NestedPriorityModelSerializer,
    _NestedPublicStatusModelSerializer,
    _NestedReporterModelSerializer,
    _NestedStatusModelSerializer,
    _NestedTypeModelSerializer
)
from signals.apps.api.v1.validation import AddressValidationMixin
from signals.apps.api.v1.validators.extra_properties import ExtraPropertiesValidator
from signals.apps.signals import workflow
from signals.apps.signals.models import Priority, Signal


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

    has_attachments = serializers.SerializerMethodField()

    extra_properties = SignalExtraPropertiesField(
        required=False,
        validators=[
            ExtraPropertiesValidator(filename=os.path.join(
                os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json')
            )
        ]
    )  # noqa

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
        )
        read_only_fields = (
            'id',
            'has_attachments',
        )

    def get_has_attachments(self, obj):
        return obj.attachments.exists()

    def update(self, instance, validated_data):
        """
        Perform update on nested models.

        Note:
        - Reporter cannot be updated via the API.
        - Atomic update (all fail/succeed), django signals on full success (see
          underlying update_multiple method of actions SignalManager).
        """
        user_email = self.context['request'].user.email

        for _property in ['location', 'status', 'category_assignment', 'priority']:
            if _property in validated_data:
                data = validated_data[_property]
                data['created_by'] = user_email

        type_data = validated_data.pop('type_assignment', {'name': 'SIG'})
        type_data['created_by'] = user_email
        validated_data['type'] = type_data

        if 'notes' in validated_data and validated_data['notes']:
            note_data = validated_data['notes'][0]
            note_data['created_by'] = user_email

        signal = Signal.actions.update_multiple(validated_data, instance)
        return signal


class PrivateSignalSerializerList(HALSerializer, AddressValidationMixin):
    """
    This serializer is used for the list endpoint and when creating a new instance
    """
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

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

    has_attachments = serializers.SerializerMethodField()

    extra_properties = SignalExtraPropertiesField(
        required=False,
        validators=[
            ExtraPropertiesValidator(
                filename=os.path.join(
                    os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json')
            )
        ]
    )

    class Meta:
        model = Signal
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
        )
        read_only_fields = (
            'created_at',
            'updated_at',
            'has_attachments',
        )
        extra_kwargs = {
            'source': {'validators': [SignalSourceValidator()]},
        }

    def get_has_attachments(self, obj):
        return obj.attachments.exists()

    def create(self, validated_data):
        if validated_data.get('status') is not None:
            raise serializers.ValidationError("Status cannot be set on initial creation")

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

        signal = Signal.actions.create_initial(
            validated_data,
            location_data,
            INITIAL_STATUS,
            category_assignment_data,
            reporter_data,
            priority_data,
            type_data
        )
        return signal


class PublicSignalSerializerDetail(HALSerializer):
    status = _NestedPublicStatusModelSerializer(required=False)
    serializer_url_field = PublicSignalLinksField
    _display = DisplayField()

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'signal_id',
            'status',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
        )


class PublicSignalCreateSerializer(serializers.ModelSerializer):
    """
    This serializer allows anonymous users to report `signals.Signals`.
    """
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment')
    priority = _NestedPriorityModelSerializer(required=False, read_only=True)
    attachments = _NestedAttachmentModelSerializer(many=True, read_only=True)

    extra_properties = SignalExtraPropertiesField(
        required=False,
        validators=[
            ExtraPropertiesValidator(
                filename=os.path.join(
                    os.path.dirname(__file__), '..', 'json_schema', 'extra_properties.json'
                )
            )
        ]
    )

    incident_date_start = serializers.DateTimeField()

    class Meta(object):
        model = Signal
        fields = (
            'id',
            'signal_id',
            'source',
            'text',
            'text_extra',
            'location',
            'category',
            'reporter',
            'status',
            'priority',
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'image',
            'attachments',
            'extra_properties',
        )
        read_only_fields = (
            'id',
            'signal_id',
            'created_at',
            'updated_at',
            'status',
            'image'
            'attachments',
        )
        extra_kwargs = {
            'id': {'label': 'ID'},
            'signal_id': {'label': 'SIGNAL_ID'},
            'source': {'validators': [SignalSourceValidator()]},
        }

    def create(self, validated_data):
        if validated_data.get('status') is not None:
            raise serializers.ValidationError("Status cannot be set on initial creation")

        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        category_assignment_data = validated_data.pop('category_assignment')

        status_data = {"state": workflow.GEMELD}
        signal = Signal.actions.create_initial(
            validated_data, location_data, status_data, category_assignment_data, reporter_data)
        return signal


class SignalIdListSerializer(HALSerializer):
    class Meta:
        model = Signal
        fields = (
            'id',
        )
