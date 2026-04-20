from django.urls import path

from signals.apps.classification.views import MlPredictCategoryView

urlpatterns = [
    path('category/prediction', MlPredictCategoryView.as_view(), name='ml-tool-predict-proxy'),
]