import os

from datapunt_api.rest import DisplayField, HALSerializer
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from signals.apps.api.generics.permissions import (
    SIAPermissions,
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
from signals.apps.api.v1.fields.attachment import PrivateSignalAttachmentRelatedField
from signals.apps.api.v1.fields.extra_properties import SignalExtraPropertiesField
from signals.apps.api.v1.serializers.nested import (
    _NestedCategoryModelSerializer,
    _NestedDepartmentModelSerializer,
    _NestedLocationModelSerializer,
    _NestedNoteModelSerializer,
    _NestedPriorityModelSerializer,
    _NestedPublicStatusModelSerializer,
    _NestedReporterModelSerializer,
    _NestedSignalDepartmentsModelSerializer,
    _NestedStatusModelSerializer,
    _NestedTypeModelSerializer,
    _NestedUserModelSerializer
)
from signals.apps.api.v1.validation.address.mixin import AddressValidationMixin
from signals.apps.api.v1.validation.mixin import SignalValidationMixin
from signals.apps.api.v1.validators.extra_properties import ExtraPropertiesValidator
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
        if signal.is_child():
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

    signal_departments = _NestedSignalDepartmentsModelSerializer(
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    user_assignment = _NestedUserModelSerializer(
        source='user_assignment.user',
        many=False,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    has_attachments = serializers.SerializerMethodField()

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
            'signal_departments',
            'attachments',
            'user_assignment',
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
        if not instance.is_parent() and validated_data.get('directing_departments_assignment') is not None:
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

        if 'signal_departments' in validated_data and validated_data['signal_departments']:
            for relation in validated_data['signal_departments']:
                relation['created_by'] = user_email

        if 'user_assignment' in validated_data and validated_data['user_assignment']:
            validated_data['user_assignment']['created_by'] = user_email

        signal = Signal.actions.update_multiple(validated_data, instance)
        return signal


class PrivateSignalSerializerList(SignalValidationMixin, HALSerializer):
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

    directing_departments = _NestedDepartmentModelSerializer(
        source='directing_departments_assignment.departments',
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    signal_departments = _NestedSignalDepartmentsModelSerializer(
        many=True,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    user_assignment = _NestedUserModelSerializer(
        source='user_assignment.user',
        many=False,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    has_attachments = serializers.SerializerMethodField()

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
    has_children = serializers.SerializerMethodField()

    attachments = PrivateSignalAttachmentRelatedField(view_name='private-signals-attachments-detail', many=True,
                                                      required=False, read_only=False, write_only=True,
                                                      queryset=Attachment.objects.all())

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
            'signal_departments',
            'attachments',
            'parent',
            'has_children',
            'user_assignment',
            'parent'
        )
        read_only_fields = (
            'created_at',
            'updated_at',
            'has_attachments',
            'has_children',
        )
        extra_kwargs = {
            'source': {'validators': [SignalSourceValidator()]},
        }

    def get_has_attachments(self, obj):
        return obj.attachments.exists()

    def get_has_children(self, obj):
        return obj.children.exists()

    def validate(self, attrs):
        errors = {}
        if attrs.get('directing_departments_assignment') is not None:
            errors.update(
                {'directing_departments_assignment': ['Directing departments cannot be set on initial creation']}
            )

        if attrs.get('signal_departments') is not None:
            errors.update(
                {'signal_departments': ['Signal departments relation cannot be set on initial creation']}
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

        if errors:
            raise serializers.ValidationError(errors)

        return super(PrivateSignalSerializerList, self).validate(attrs=attrs)

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

        signal = Signal.actions.create_initial(
            validated_data,
            location_data,
            INITIAL_STATUS,
            category_assignment_data,
            reporter_data,
            priority_data,
            type_data
        )

        if attachments:
            Signal.actions.copy_attachments(data=attachments, signal=signal)

        signal.refresh_from_db()
        return signal


class PublicSignalSerializerDetail(HALSerializer):
    status = _NestedPublicStatusModelSerializer(required=False)
    serializer_url_field = PublicSignalLinksField
    _display = serializers.SerializerMethodField(method_name='get__display')

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
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    category = _NestedCategoryModelSerializer(source='category_assignment')

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

    incident_date_start = serializers.DateTimeField()

    class Meta(object):
        model = Signal
        fields = (
            'text',
            'text_extra',
            'location',
            'category',
            'reporter',
            'incident_date_start',
            'incident_date_end',
            'extra_properties',
        )

    def validate(self, data):
        """Make sure any extra data is rejected"""
        if hasattr(self, 'initial_data'):
            present_keys = set(self.initial_data)
            allowed_keys = set(self.fields)

            if present_keys - allowed_keys:
                raise ValidationError('Extra properties present: {}'.format(
                    ', '.join(present_keys - allowed_keys)
                ))
        return super(PublicSignalCreateSerializer, self).validate(data)

    def create(self, validated_data):
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


class SignalGeoSerializer(GeoFeatureModelSerializer):
    # For use with the "geography" action
    location = GeometryField(source='location.geometrie')

    class Meta:
        model = Signal
        id_field = False
        geo_field = 'location'
        fields = ['id', 'created_at']


class AbridgedChildSignalSerializer(HALSerializer):
    serializer_url_field = PrivateSignalLinksField

    status = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = (
            '_links',
            'id',
            'status',
            'category',
            'updated_at',
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
