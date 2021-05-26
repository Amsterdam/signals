# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from signals.apps.api import app_settings
from signals.apps.api.fields import PrivateSignalWithContextLinksField
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class SignalContextReporterSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()
    can_view_signal = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = (
            'id',
            'created_at',
            'category',
            'status',
            'feedback',
            'can_view_signal',
            'has_children',
        )

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

    def get_status(self, obj):
        return {'state': obj.status.state, 'state_display': obj.status.get_state_display(), }

    def get_feedback(self, obj):
        """
        Returns the lastest feedback object if it exists else None
        """
        if obj.feedback.exists():
            latest_feedback = obj.feedback.first()
            return {'is_satisfied': latest_feedback.is_satisfied, 'submitted_at': latest_feedback.submitted_at, }

    def get_can_view_signal(self, obj):
        return Signal.objects.filter(pk=obj.pk).filter_for_user(self.context['request'].user).exists()

    def get_has_children(self, obj):
        return obj.children.exists()


class SignalContextSerializer(HALSerializer):
    serializer_url_field = PrivateSignalWithContextLinksField

    near = serializers.SerializerMethodField(method_name='get_near')
    reporter = serializers.SerializerMethodField(method_name='get_reporter')

    class Meta:
        model = Signal
        fields = (
            '_links',
            'near',
            'reporter',
        )

    def get_near(self, obj):
        signals_for_geography_qs = Signal.objects.annotate(
            distance_from_point=Distance('location__geometrie', obj.location.geometrie),
        ).filter(
            (Q(parent__isnull=True) & Q(children__isnull=True)) | Q(parent__isnull=False),
            distance_from_point__lte=app_settings.SIGNAL_CONTEXT_GEOGRAPHY_RADIUS,
            category_assignment__category_id=obj.category_assignment.category.pk,
            created_at__gte=(
                timezone.now() - timezone.timedelta(weeks=app_settings.SIGNAL_CONTEXT_GEOGRAPHY_CREATED_DELTA_WEEKS)
            ),
        ).exclude(pk=obj.pk)

        return {
            'signal_count': signals_for_geography_qs.count(),
        }

    def get_reporter(self, obj):
        if not obj.reporter.email:
            return None

        reporter_email = obj.reporter.email

        signals_for_reporter_count = Signal.objects.filter_reporter(
            email=reporter_email
        ).filter(parent__isnull=True).count()
        open_signals_for_reporter_count = Signal.objects.filter_reporter(email=reporter_email).exclude(
            status__state__in=[workflow.GEANNULEERD, workflow.AFGEHANDELD, workflow.GESPLITST]
        ).filter(parent__isnull=True).count()
        # Not filtering parent__isnull=True, as feedback is not requested for child signals.
        satisfied_count = Signal.objects.reporter_feedback_satisfied_count(email=reporter_email)
        not_satisfied_count = Signal.objects.reporter_feedback_not_satisfied_count(email=reporter_email)

        return {
            'signal_count': signals_for_reporter_count,
            'open_count': open_signals_for_reporter_count,
            'positive_count': satisfied_count,
            'negative_count': not_satisfied_count,
        }


class SignalContextGeoSerializer(GeoFeatureModelSerializer):
    location = GeometryField(source='location.geometrie')

    class Meta:
        model = Signal
        id_field = False
        geo_field = 'location'
        fields = ['id', 'created_at']

    def get_properties(self, instance, fields):
        properties = super(SignalContextGeoSerializer, self).get_properties(instance, fields)
        properties.update({
            'status': {
                'state': instance.status.state,
                'state_display': instance.status.get_state_display(),
            }
        })
        return properties
