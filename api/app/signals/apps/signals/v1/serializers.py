"""
Serializsers that are used exclusively by the V1 API
"""
import copy
from collections import OrderedDict

from datapunt_api.rest import DisplayField, HALSerializer
from django.urls import resolve
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from signals import settings
from signals.apps.signals import workflow
from signals.apps.signals.address.validation import (
    AddressValidation,
    AddressValidationUnavailableException,
    NoResultsException
)
from signals.apps.signals.api_generics.exceptions import PreconditionFailed
from signals.apps.signals.api_generics.validators import NearAmsterdamValidatorMixin
from signals.apps.signals.models import (
    Attachment,
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
    PrivateSignalAttachmentLinksField,
    PrivateSignalLinksField,
    PrivateSignalLinksFieldWithArchives,
    PrivateSignalSplitLinksField,
    PublicSignalAttachmentLinksField,
    PublicSignalLinksField,
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
            'bag_validated',
        )
        read_only_fields = (
            'id',
            'created_by',
            'bag_validated',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }


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
            'created_at',
            'user',
        )

    def validate(self, attrs):
        if (attrs['state'] == workflow.TE_VERZENDEN
                and attrs.get('target_api') == Status.TARGET_API_SIGMAX):

            request = self.context.get('request')
            if request and not request.user.has_perm('signals.push_to_sigmax'):
                raise PermissionDenied({
                    'state': "You don't have permissions to push to Sigmax/CityControl."
                })

        return super(_NestedStatusModelSerializer, self).validate(attrs=attrs)


class _NestedPublicStatusModelSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Status
        fields = (
            'id',
            'state',
            'state_display',
        )
        read_only_fields = (
            'id',
            'state',
            'state_display',
        )


class _NestedCategoryModelSerializer(serializers.ModelSerializer):
    sub_category = SubCategoryHyperlinkedRelatedField(write_only=True, required=True)
    sub = serializers.CharField(source='sub_category.name', read_only=True)
    sub_slug = serializers.CharField(source='sub_category.slug', read_only=True)
    main = serializers.CharField(source='sub_category.main_category.name', read_only=True)
    main_slug = serializers.CharField(source='sub_category.main_category.slug', read_only=True)

    category_url = serializers.SerializerMethodField(read_only=True)

    departments = serializers.SerializerMethodField(
        source='sub_category.departments',
        read_only=True
    )

    class Meta:
        model = CategoryAssignment
        fields = (
            'category_url',
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'sub_category',
            'departments',
            'created_by',
        )
        read_only_fields = (
            'created_by',
            'departments',
        )

    def get_departments(self, obj):
        return ', '.join(obj.sub_category.departments.values_list('code', flat=True))

    def get_category_url(self, obj):
        from rest_framework.reverse import reverse
        request = self.context['request'] if 'request' in self.context else None
        return reverse(
            'v1:sub-category-detail',
            kwargs={
                'slug': obj.sub_category.main_category.slug,
                'sub_slug': obj.sub_category.slug,
            },
            request=request
        )


class _NestedReporterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporter
        fields = (
            'email',
            'phone',
        )


class _NestedPriorityModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = (
            'priority',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )


class _NestedNoteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = (
            'text',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )


class _NestedAttachmentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = (
            'file',
            'created_at',
            'is_image',
        )


class AddressValidationMixin():
    def validate_location(self, location_data):
        """Validate location data used in creation and update of Signal instances"""
        # Validate address, but only if it is present in input. SIA must also
        # accept location data without address but with coordinates.
        if 'geometrie' not in location_data:
            raise ValidationError('Coordinate data must be present')
        if 'address' in location_data and location_data['address']:
            try:
                address_validation = AddressValidation()
                validated_address = address_validation.validate_address_dict(
                    location_data["address"])

                # Set suggested address from AddressValidation as address and save original address
                # in extra_properties, to correct possible spelling mistakes in original address.
                if ("extra_properties" not in location_data or
                        location_data['extra_properties'] is None):
                    location_data["extra_properties"] = {}

                location_data["extra_properties"]["original_address"] = location_data["address"]
                location_data["address"] = validated_address
                location_data["bag_validated"] = True

            except AddressValidationUnavailableException:
                # Ignore it when the address validation is unavailable. Just save the unvalidated
                # location.
                pass
            except NoResultsException:
                raise ValidationError({"location": "Niet-bestaand adres."})

        return location_data


class PrivateSignalSerializerDetail(HALSerializer, AddressValidationMixin):
    serializer_url_field = PrivateSignalLinksFieldWithArchives
    _display = DisplayField()
    image = serializers.ImageField(read_only=True)

    location = _NestedLocationModelSerializer(required=False)
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment', required=False)
    reporter = _NestedReporterModelSerializer(required=False)
    priority = _NestedPriorityModelSerializer(required=False)
    notes = _NestedNoteModelSerializer(many=True, required=False)
    attachments = _NestedAttachmentModelSerializer(many=True, read_only=True)

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'category',
            'id',
            'image',
            'attachments',
            'location',
            'status',
            'reporter',
            'priority',
            'notes',
        )
        read_only_fields = (
            'id',
            'image',
            'attachments',
        )

    def _update_location(self, instance, validated_data):
        """
        Update the location of a Signal using the action manager
        """
        if 'location' in validated_data:
            location_data = validated_data.pop('location')
            location_data['created_by'] = self.context['request'].user.email

            Signal.actions.update_location(location_data, instance)

    def _update_status(self, instance, validated_data):
        """
        Update the status of a Signal using the action manager
        """
        if 'status' in validated_data:
            status_data = validated_data.pop('status')
            status_data['created_by'] = self.context['request'].user.email

            Signal.actions.update_status(status_data, instance)

    def _update_category_assignment(self, instance: Signal, validated_data):
        """
        Update the category assignment of a Signal using the action manager
        """
        category_assignment_data = validated_data['category_assignment']
        category_assignment_data['created_by'] = self.context['request'].user.email

        Signal.actions.update_category_assignment(category_assignment_data, instance)

    def _update_priority(self, instance, validated_data):
        """
        Update the priority of a Signal using the action manager
        """
        priority_data = validated_data['priority']
        priority_data['created_by'] = self.context['request'].user.email

        Signal.actions.update_priority(priority_data, instance)

    def _update_notes(self, instance, validated_data):
        """
        Not really updating notes, we are only adding new notes

        Note: For now we only allow the creation of only one note through the API, it still needs
              to be provided as a list though :(
        """
        if 'notes' in validated_data and len(validated_data['notes']) > 0:
            note_data = validated_data['notes'][0]
            note_data['created_by'] = self.context['request'].user.email

            Signal.actions.create_note(note_data, instance)

    def update(self, instance, validated_data):
        """
        Perform update on nested models.

        Note: Reporter cannot be updated via the API.
        """
        if 'location' in validated_data:
            self._update_location(instance, validated_data)

        if 'status' in validated_data:
            self._update_status(instance, validated_data)

        if 'category_assignment' in validated_data:
            self._update_category_assignment(instance, validated_data)

        if 'priority' in validated_data:
            self._update_priority(instance, validated_data)

        if 'notes' in validated_data:
            self._update_notes(instance, validated_data)

        return instance


class PrivateSignalSerializerList(HALSerializer, AddressValidationMixin):
    serializer_url_field = PrivateSignalLinksField
    _display = DisplayField()

    image = serializers.ImageField(read_only=True)

    location = _NestedLocationModelSerializer()
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment')
    reporter = _NestedReporterModelSerializer()
    priority = _NestedPriorityModelSerializer(required=False)
    notes = _NestedNoteModelSerializer(many=True, required=False)
    attachments = _NestedAttachmentModelSerializer(many=True, read_only=True)

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
            'attachments',
            'extra_properties',
            'notes',
        )
        read_only_fields = (
            'created_at',
            'updated_at',
            'image',
            'attachments',
        )

    def create(self, validated_data):
        if validated_data.get('status') is not None:
            raise ValidationError("Status can not be set on initial creation")

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


class _NestedSplitSignalSerializer(HALSerializer):
    serializer_url_field = PrivateSignalLinksField
    reuse_parent_image = serializers.BooleanField(default=False, write_only=True)
    category = _NestedCategoryModelSerializer(required=True, source='category_assignment')

    class Meta:
        model = Signal
        fields = (
            'id',
            'text',
            'reuse_parent_image',
            'category',
            '_links',
        )
        read_only_fields = (
            'id',
            '_links',
        )


class PrivateSplitSignalSerializer(serializers.Serializer):
    def validate(self, data):
        return self.to_internal_value(data)

    def to_internal_value(self, data):
        potential_parent_signal = self.context['view'].get_object()

        if potential_parent_signal.status.state == workflow.GESPLITST:
            raise PreconditionFailed("Signal has already been split")
        if potential_parent_signal.is_child():
            raise PreconditionFailed("A child signal cannot itself be split.")

        serializer = _NestedSplitSignalSerializer(data=data, many=True, context=self.context)
        serializer.is_valid()

        errors = OrderedDict()
        if not settings.SIGNAL_MIN_NUMBER_OF_CHILDREN <= len(
                self.initial_data) <= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            errors["children"] = 'A signal can only be split into min {} and max {} signals'.format(
                settings.SIGNAL_MIN_NUMBER_OF_CHILDREN, settings.SIGNAL_MAX_NUMBER_OF_CHILDREN
            )

        if errors:
            raise ValidationError(errors)

        # TODO: find a cleaner solution to the sub category handling.
        output = {"children": copy.deepcopy(self.initial_data)}

        for item in output["children"]:
            sub_category_url = item['category']['sub_category']

            from urllib.parse import urlparse
            path = (urlparse(sub_category_url)).path

            view, args, kwargs = resolve(path)  # noqa
            sub_category = SubCategory.objects.get(
                slug=kwargs['sub_slug'],  # Check the urls.py for why!
                main_category__slug=kwargs['slug'],
            )
            item['category']['sub_category'] = sub_category

        return output

    def to_representation(self, signal):
        if signal.children.count() == 0:
            raise NotFound("Split signal not found")

        links_field = PrivateSignalSplitLinksField(self.context['view'])
        nss = _NestedSplitSignalSerializer(signal.children.all(), many=True)

        return {
            "_links": links_field.to_representation(signal),
            "children": nss.data,
        }

    def create(self, validated_data):
        signal = Signal.actions.split(split_data=validated_data["children"],
                                      signal=self.context['view'].get_object())

        return signal


class SignalAttachmentSerializer(HALSerializer):
    _display = DisplayField()
    location = serializers.FileField(source='file', required=False)

    class Meta:
        model = Attachment
        fields = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
            'file',
        )

        read_only = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
        )

        extra_kwargs = {'file': {'write_only': True}}

    def create(self, validated_data):
        attachment = Signal.actions.add_attachment(validated_data['file'],
                                                   self.context['view'].get_object())

        if self.context['request'].user:
            attachment.created_by = self.context['request'].user.email
            attachment.save()

        return attachment

    def validate_file(self, file):
        if file.size > 8388608:  # 8MB = 8*1024*1024
            raise ValidationError("Bestand mag maximaal 8Mb groot zijn.")
        return file


class PublicSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField


class PrivateSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField


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
    location = _NestedLocationModelSerializer()
    reporter = _NestedReporterModelSerializer()
    status = _NestedStatusModelSerializer(required=False)
    category = _NestedCategoryModelSerializer(source='category_assignment')
    priority = _NestedPriorityModelSerializer(required=False, read_only=True)
    attachments = _NestedAttachmentModelSerializer(many=True, read_only=True)

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
        }

    def create(self, validated_data):
        if validated_data.get('status') is not None:
            raise ValidationError("Status can not be set on initial creation")

        location_data = validated_data.pop('location')
        reporter_data = validated_data.pop('reporter')
        category_assignment_data = validated_data.pop('category_assignment')

        status_data = {"state": workflow.GEMELD}
        signal = Signal.actions.create_initial(
            validated_data, location_data, status_data, category_assignment_data, reporter_data)
        return signal
