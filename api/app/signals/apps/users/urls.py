from django.urls import include, path

urlpatterns = [
    path('v1/', include(('signals.apps.users.v1.urls', 'users'), namespace='v1')),
    path('', include(('signals.apps.users.v0.urls', 'users'), namespace='v0')),
]
