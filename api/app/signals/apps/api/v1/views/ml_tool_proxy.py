from django.core.exceptions import ValidationError as DjangoCoreValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.ml_tool.proxy.client import MLToolClient
from signals.apps.api.ml_tool.utils import get_clean_category_url, get_url_from_category
from signals.apps.signals.models import Category


class LegacyMlPredictCategoryView(APIView):
    ml_tool_client = MLToolClient()

    def post(self, request, *args, **kwargs):
        # Default empty response
        data = {'hoofdrubriek': [], 'subrubriek': []}

        try:
            response = self.ml_tool_client.predict(text=request.data['text'])
        except DjangoCoreValidationError as e:
            raise ValidationError(e.message, e.code)
        else:
            if response.status_code == 200:
                response_data = response.json()

                for key in data.keys():
                    category_url, category_exists = get_clean_category_url(
                        category_url=response_data[key][0][0], request=self.request
                    )
                    if not category_exists:
                        # When we cannot translate we return the 'overig-overig' category url
                        default_category = Category.objects.get(
                            slug='overig',
                            parent__isnull=False,
                            parent__slug='overig'
                        )
                        category_url = get_url_from_category(default_category, request=self.request)

                    data[key].append([category_url])
                    data[key].append([response_data[key][1][0]])

        return Response(data)
