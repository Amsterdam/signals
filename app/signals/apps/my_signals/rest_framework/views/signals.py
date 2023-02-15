# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DEFAULT_RENDERERS
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.db.models import Min, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.history.models import Log
from signals.apps.my_signals.rest_framework.authentication import MySignalsTokenAuthentication
from signals.apps.my_signals.rest_framework.filters.signals import MySignalFilterSet
from signals.apps.my_signals.rest_framework.serializers.signals import (
    HistoryLogHalSerializer,
    SignalDetailSerializer,
    SignalListSerializer
)
from signals.apps.signals import workflow
from signals.apps.signals.models import (
    CategoryAssignment,
    Location,
    Note,
    Priority,
    Signal,
    SignalDepartments,
    SignalUser,
    Status,
    Type
)


class MySignalsViewSet(DetailSerializerMixin, ReadOnlyModelViewSet):
    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination

    authentication_classes = (MySignalsTokenAuthentication, )

    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    serializer_class = SignalListSerializer
    serializer_detail_class = SignalDetailSerializer

    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filterset_class = MySignalFilterSet

    ordering = (
        '-created_at',
    )
    ordering_fields = (
        'created_at',
    )

    def get_queryset(self, *args, **kwargs):
        """
        Only return signals that are in a specific state and created in the last year
        """
        one_year_ago = timezone.now() - relativedelta(years=1)

        return Signal.objects.filter(
            reporter__email__iexact=self.request.user.email,  # Only select Signals for the logged in reporter
            created_at__gte=one_year_ago  # Only signals from the last 12 months
        ).exclude(
            parent__isnull=False  # Exclude all child signals
        )

    @action(detail=True, url_path=r'history/?$')
    def history(self, *args, **kwargs):
        """
        The public history view of a signal  

        This will return the history log of a Signal for the "My Signal" flow.  
        Not all history will be returned to the reporter.  

        The following rules apply:  
        - Do not return logs about SignalDepartments (Department assignment)  
        - Do not return logs about SignalUser (User assignment)  
        - Do not return logs about Note  
        - Do not return logs about Priority  
        - Do not return logs about Status changes to LEEG, AFWACHTING, ON_HOLD, GEANNULEERD, GESPLITST, 
          VERZOEK_TOT_AFHANDELING, INGEPLAND, VERZOEK_TOT_HEROPENEN, TE_VERZENDEN, VERZONDEN, VERZENDEN_MISLUKT, 
          AFGEHANDELD_EXTERN  
        - Status changes are translated to a more reporter friendly name  
        -- GEANNULEERD, AFGEHANDELD -> Afgesloten    
        -- HEROPEND -> Heropend  
        -- REACTIE_GEVRAAGD -> Vraag aan u verstuurd  
        -- REACTIE_ONTVANGEN -> Antwoord van u ontvangen    
        -- All other statusses -> Open  
        - Do not return the first occurrences of logs about CategoryAssignment, Location and Type    
        """  # noqa
        signal = self.get_object()

        # Note and Priority ContentTypes are always excluded
        excluded_content_types = ContentType.objects.get_for_models(Note, Priority, SignalDepartments, SignalUser)
        excluded_q = Q(content_type__in=excluded_content_types.values())

        # Some Status transactions are excluded
        status_type = ContentType.objects.get_for_model(Status)
        excluded_q |= Q(Q(content_type=status_type) & Q(extra__in=[workflow.LEEG, workflow.AFWACHTING, workflow.ON_HOLD,
                                                                   workflow.GEANNULEERD, workflow.GESPLITST,
                                                                   workflow.VERZOEK_TOT_AFHANDELING, workflow.INGEPLAND,
                                                                   workflow.VERZOEK_TOT_HEROPENEN,
                                                                   workflow.TE_VERZENDEN, workflow.VERZONDEN,
                                                                   workflow.VERZENDEN_MISLUKT,
                                                                   workflow.AFGEHANDELD_EXTERN, ]))

        # The first occurrence in the history log of a Location, CategoryAssignment or Type transition are excluded
        exclude_first_occurrence_content_types = ContentType.objects.get_for_models(Location, CategoryAssignment, Type)
        excluded_q |= Q(id__in=signal.history_log.values(
            'content_type_id'
        ).filter(
            content_type_id__in=exclude_first_occurrence_content_types.values()
        ).annotate(
            id=Min('id')
        ).values_list(
            'id',
            flat=True
        ).order_by())

        history_log_qs = signal.history_log.exclude(Q(excluded_q))

        what = self.request.query_params.get('what', None)
        if what:
            _action = Log.translate_what_to_action(what)
            _content_type = Log.translate_what_to_content_type(what)
            history_log_qs = history_log_qs.filter(action__iexact=_action, content_type__model__iexact=_content_type)

        ordering = self.request.query_params.get('ordering', None)
        if ordering and (ordering == 'created_at' or ordering == '-created_at'):
            history_log_qs = history_log_qs.order_by(ordering)

        serializer = HistoryLogHalSerializer(history_log_qs, many=True)
        return Response(serializer.data)
