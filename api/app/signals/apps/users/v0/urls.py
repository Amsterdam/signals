from django.urls import path

from signals.apps.users.v0.views import UserMeView

urlpatterns = [
    # DEPRECATED url route for `auth/me`. Should be fixed in the frontend before we can remove
    # this endpoint here.
    path('auth/me/', UserMeView.as_view()),
    path('user/auth/me/', UserMeView.as_view())
]
