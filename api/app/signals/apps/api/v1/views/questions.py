from datapunt_api.rest import DatapuntViewSet, HALPagination
from django.db.models import Q

from signals.apps.api.v1.serializers import PublicQuestionSerializerDetail
from signals.apps.signals.models import Question


class PublicQuestionViewSet(DatapuntViewSet):
    queryset = Question.objects.all()

    serializer_class = PublicQuestionSerializerDetail
    serializer_detail_class = PublicQuestionSerializerDetail
    pagination_class = HALPagination
    view_name = 'question-detail'

    def get_queryset(self, *args, **kwargs):
        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            childq = Q(category__parent__slug=self.kwargs['slug']) & Q(category__slug=self.kwargs['sub_slug'])
            parentq = Q(category__parent=None) & Q(category__slug=self.kwargs['slug'])
            return self.queryset.filter(
                childq | parentq
            )
        else:
            return self.queryset.filter(
                category__parent=None,
                category__slug=self.kwargs['slug']
            )
