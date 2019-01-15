from django.urls import path

from signals.apps.dashboards import views

urlpatterns = [
    path('1', views.DashboardProtype.as_view()),
]
