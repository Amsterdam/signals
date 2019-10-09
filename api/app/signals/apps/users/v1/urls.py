from django.urls import include, path

from signals.apps.users.v1.views import PingView

urlpatterns = [
    path('private/', include([
        path('users/', PingView.as_view()),
        path('roles/', PingView.as_view()),
        path('permissions/', PingView.as_view()),
    ]))
]
