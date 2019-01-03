from django.urls import path

from signals.apps.health import views

urlpatterns = [
    path('health', views.health),
    path('data', views.check_data),
    path('data/categories', views.check_categories),
]
