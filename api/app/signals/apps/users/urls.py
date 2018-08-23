from django.urls import path

from signals.apps.users.views import UserView

urlpatterns = [
    path('auth/me/', UserView.as_view()),
]
