"""
Serializsers that are used exclusively by the V1 API
"""
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.signals import workflow
from signals.apps.signals.api_generics.validators import NearAmsterdamValidatorMixin
from signals.apps.signals.models import (
    CategoryAssignment,
    History,
    Location,
    MainCategory,
    Note,
    Priority,
    Reporter,
    Signal,
    Status,
    SubCategory
)
from signals.apps.signals.v0.serializers import _NestedDepartmentSerializer
from signals.apps.signals.v1.fields import (
    MainCategoryHyperlinkedIdentityField,
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    SubCategoryHyperlinkedIdentityField,
    SubCategoryHyperlinkedRelatedField
)


class SubCategoryHALSerializer(HALSerializer):
    serializer_url_field = SubCategoryHyperlinkedIdentityField
    _display = DisplayField()
    departments = _NestedDepartmentSerializer(many=True)

    class Meta:
        model = SubCategory
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'handling',
            'departments',
            'is_active',
        )


class MainCategoryHALSerializer(HALSerializer):
    serializer_url_field = MainCategoryHyperlinkedIdentityField
    _display = DisplayField()
    sub_categories = SubCategoryHALSerializer(many=True)

    class Meta:
        model = MainCategory
        fields = (
            '_links',
            '_display',
            'name',
            'slug',
            'sub_categories',
        )


# -- /private API serializers --

class HistoryHalSerializer(HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    who = serializers.SerializerMethodField()

    def get_who(self, obj):
        """Generate string to show in UI, missing users are set to default."""
        if obj.who is None:
            return 'SIA systeem'
        return obj.who

    class Meta:
        model = History
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )


class _NestedLocationModelSerializer(NearAmsterdamValidatorMixin, serializers.ModelSerializer):

    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'id',
            'stadsdeel',
            'buurt_code',
            'address',
            'address_text',
            'geometrie',
            'extra_properties',
            'created_by',
        )
        read_only_fields = (
            'id',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }

# TODO: extend _NestedStatusModelSerializer with validate method like that one in
# signals.apps.signals.v0.serializers.StatusHALSerializer (i.e. check permissions ...)
class _NestedStatusModelSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Status
        fields = (
            'text',
            'user',
            'state',
            'state_display',
            'extra_properties',
            'created_at',
        )
        read_only_fields = (
            'state',
            'created_at',
        )


class _NestedCategoryModelSerializer(serializers.ModelSerializer):
    sub_category = SubCategoryHyperlinkedRelatedField(write_only=True, required=True)
    sub = serializers.CharField(source='sub_category.name', read_only=True)
    sub_slug = serializers.CharField(source='sub_category.slug', read_only=True)
    main = serializers.CharField(source='sub_category.main_category.name', read_only=True)
    main_slug = serializers.CharField(source='sub_category.main_category.slug', read_only=True)

    departments = serializers.SerializerMethodField(
        source='sub_category.departments',
        read_only=True
    )

    class Meta:
        model = CategoryAssignment
        fields = (
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'sub_category',
            'departments',
            'created_by',
        )

    def get_departments(self, obj):
        return ', '.join(obj.sub_category.departments.values_list('code', flat=True))


class _NestedReporterModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
            'extra_properties',
        )


class _NestedPriorityModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = (
            'priority',
            'created_by',
        )


class _NestedNoteModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = (
            'text',
            'created_at',
            'created_by',
        )


class PrivateSignalSerializerDetail(HALSerializer):
    serializer_url_field = PrivateSignalLinksFieldWithArchives
    _display = DisplayField()
    image = serializers.ImageField(read_only=True)

    location = _NestedLocationModelSerializer(required=False)
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment', required=False)
    reporter = _NestedReporterModelSerializer(required=False)
    priority = _NestedPriorityModelSerializer(required=False)
    notes = _NestedNoteModelSerializer(many=True, required=False)

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'category',
            'id',
            'image',
            'location',
            'status',
            'reporter',
            'priority',
            'notes',
        )
        read_only_fields = (
            'id',
            'image',
        )

    def update(self, instance, validated_data):
        """
        Perform update on nested models.

        Note: Reporter cannot be updated via the API.
        """
        print(validated_data.keys())
        user_email = self.context['request'].user.email

        if 'location' in validated_data:
            location_data = validated_data.pop('location')
            location_data['created_by'] = user_email

            Signal.actions.update_location(
                location_data,
                instance,
            )
        # TODO: see comment above _NestedStatusModelSerializer in this module 
        # TODO: consider renaming user property to created_by for symmetry
        if 'status' in validated_data:
            status_data = validated_data.pop('status')
            status_data['user'] = user_email
    
            Signal.actions.update_status(
                status_data,
                instance,
            )
        # TODO: fix problem with SubCategory URL, see failing test
        if 'category' in validated_data:
            category_data = validated_data['category']
            category_data['created_by'] = user_email

            Signal.actions.update_category_assignment(
                category_data,
                instance,
            )
        if 'priority' in validated_data:
            priority_data = validated_data['priority']
            priority_data['created_by'] = user_email

            Signal.actions.update_priority(
                priority_data,
                instance,
            )
        if 'note' in validated_data:
            print("CREATE NOTE AS REQUESTED")
            note_data = validated_data['note']
            note_data['created_by'] = user_email
    
            Signal.actions.create_note(
                note_data,
                instance,
            )

        return instance


class PrivateSignalSerializerList(HALSerializer):
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

    image = serializers.ImageField(read_only=True)

    location = _NestedLocationModelSerializer()
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment')
    reporter = _NestedReporterModelSerializer()
    priority = _NestedPriorityModelSerializer(required=False)
    notes = _NestedNoteModelSerializer(many=True, required=False)

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
            'created_at',
            'updated_at',
            'incident_date_start',
            'incident_date_end',
            'operational_date',
            'image',
            'extra_properties',
            'notes',
        )
        read_only_fields = (
            'created_at',
            'updated_at',
        )

    def create(self, validated_data):
        # We ignore the status from the incoming Signal and replace it with the
        # initial state in the workflow (GEMELD).
        logged_in_user = self.context['request'].user
        INITIAL_STATUS = {
            'state': workflow.GEMELD,  # see models.py is already default
            'text': None,
            'user': logged_in_user.email,
        }
        validated_data.pop('status', None)  # Discard what was sent over the API

        # We require location and reporter to be set and to be valid.
        reporter_data = validated_data.pop('reporter')

        location_data = validated_data.pop('location')
        location_data['created_by'] = logged_in_user.email

        category_assignment_data = validated_data.pop('category_assignment')
        category_assignment_data['created_by'] = logged_in_user.email

        # We will use the priority on the incoming message if present.
        priority_data = validated_data.pop('priority', {
            'priority': Priority.PRIORITY_NORMAL
        })
        priority_data['created_by'] = logged_in_user.email

        signal = Signal.actions.create_initial(
            validated_data,
            location_data,
            INITIAL_STATUS,
            category_assignment_data,
            reporter_data,
            priority_data
        )
        return signal
