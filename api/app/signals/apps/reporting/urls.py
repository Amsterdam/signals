from django.urls import path

from signals.apps.reporting import views

urlpatterns = [
    path('horeca_csv', views.HorecaCSVExportViewSet.as_view({'get': 'list'})),
]
