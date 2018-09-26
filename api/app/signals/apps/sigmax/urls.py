from django.urls import path

from signals.apps.sigmax import views

urlpatterns = [
    path('soap', views.CityControlReceiver.as_view()),
]
