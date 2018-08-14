from django.urls import path

from . import views

urlpatterns = [path("health", views.health), path("data", views.check_data)]
