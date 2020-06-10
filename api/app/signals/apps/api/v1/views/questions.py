from datapunt_api.rest import DatapuntViewSet, HALPagination
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.v1.filters import QuestionFilterSet
from signals.apps.api.v1.serializers import PublicQuestionSerializerDetail
from signals.apps.signals.models import Question


class PublicQuestionViewSet(DatapuntViewSet):
    queryset = Question.objects.all()

    serializer_class = PublicQuestionSerializerDetail
    serializer_detail_class = PublicQuestionSerializerDetail
    pagination_class = HALPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = QuestionFilterSet

    def get_queryset(self, *args, **kwargs):
        main_slug = self.request.query_params.get('main_slug', None)
        sub_slug = self.request.query_params.get('sub_slug', None)

        # sort on main category first, then question ordering
        qs = self.queryset.filter(category__is_active=True).order_by(
            'categoryquestion__category__parent', '-categoryquestion__order'
        )

        if main_slug:
            if sub_slug:
                childq = Q(category__parent__slug=main_slug) & Q(category__slug=sub_slug)
                parentq = Q(category__parent=None) & Q(category__slug=main_slug)
                qs = qs.filter(childq | parentq)
            else:
                qs = qs.filter(
                    category__parent=None,
                    category__slug=main_slug
                )
        return qs
