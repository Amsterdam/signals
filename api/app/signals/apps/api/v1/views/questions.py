from datapunt_api.rest import DatapuntViewSet, HALPagination
from django.db.models import Q
from django.shortcuts import get_list_or_404

from signals.apps.api.v1.serializers import PublicQuestionSerializerDetail
from signals.apps.signals.models import Question


class PublicQuestionViewSet(DatapuntViewSet):
    queryset = Question.objects.all()

    serializer_class = PublicQuestionSerializerDetail
    serializer_detail_class = PublicQuestionSerializerDetail
    pagination_class = HALPagination

    def get_queryset(self, *args, **kwargs):
        queryset = self.filter_queryset(
            self.queryset.filter(category__is_active=True).order_by('-categoryquestion__order')
        )

        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            childq = Q(category__parent__slug=self.kwargs['slug']) & Q(category__slug=self.kwargs['sub_slug'])
            parentq = Q(category__parent=None) & Q(category__slug=self.kwargs['slug'])
            return get_list_or_404(queryset, childq | parentq)
        else:
            return get_list_or_404(
                queryset,
                category__parent=None,
                category__slug=self.kwargs['slug']
            )
