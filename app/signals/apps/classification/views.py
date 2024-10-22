# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.ml_tool.client import MLToolClient
from signals.apps.signals.models import Category
import pickle

from django.conf import settings
from rest_framework import status

from signals.apps.classification.models import Classifier


@extend_schema(exclude=True)
class MlPredictCategoryView(APIView):
    ml_tool_client = MLToolClient()

    _default_category_url = None
    default_category = None

    def __init__(self, *args, **kwargs):
        # When we cannot translate we return the 'overig-overig' category url
        self.default_category = Category.objects.get(slug='overig', parent__isnull=False, parent__slug='overig')

        super().__init__(*args, **kwargs)

    @property
    def default_category_url(self):
        if not self._default_category_url and self.default_category:
            request = self.request if self.request else None
            self._default_category_url = self.default_category.get_absolute_url(request=request)
        return self._default_category_url

    def get_prediction_old_ml_proxy(self, request):
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
                    try:
                        category = Category.objects.get_from_url(url=response_data[key][0][0])
                    except Category.DoesNotExist:
                        category_url = self.default_category_url
                    else:
                        category_url = category.get_absolute_url(request=request)

                    data[key].append([category_url])
                    data[key].append([response_data[key][1][0]])

        return Response(data)

    def get_prediction_new_ml_proxy(self, request, classifier):
        try:
            main_model = pickle.load(classifier.main_model)
            sub_model = pickle.load(classifier.sub_model)

            text = request.data['text']

            # Get prediction and probability for the main model
            main_prediction = main_model.predict([text])
            main_probability = main_model.predict_proba([text])

            # Get prediction and probability for the sub model
            sub_prediction = sub_model.predict([text])
            sub_probability = sub_model.predict_proba([text])

            main_slug = main_prediction[0]
            sub_slug = sub_prediction[0].split('|')[1]

            data = {
                'hoofdrubriek': [
                    [settings.BACKEND_URL + f'/signals/v1/public/terms/categories/{main_slug}'],
                    [main_probability[0][0]]
                ],
                'subrubriek': [
                    [settings.BACKEND_URL + f'/signals/v1/public/terms/categories/{main_slug}/sub_categories/{sub_slug}'],
                    [sub_probability[0][0]]
                ]
            }
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(status=status.HTTP_200_OK, data=data)

    def post(self, request, *args, **kwargs):
        try:
            classifier = Classifier.objects.get(is_active=True)
            return self.get_prediction_new_ml_proxy(request, classifier)
        except Classifier.DoesNotExist:
            return self.get_prediction_old_ml_proxy(request)




