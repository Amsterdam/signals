from django.core.exceptions import ValidationError as DjangoCoreValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.ml_tool.proxy.client import MLToolClient
from signals.apps.api.ml_tool.utils import translate_prediction_category_url


class MlPredictCategoryView(APIView):
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
                    category_url, translated = translate_prediction_category_url(
                        category_url=response_data[key][0][0], request=self.request
                    )

                    data[key].append([category_url])
                    data[key].append([response_data[key][1][0]])

        return Response(data)
