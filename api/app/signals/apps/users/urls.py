from django.urls import path

from signals.apps.users.views import UserMeView

urlpatterns = [
    path('auth/me/', UserMeView.as_view()),
]
