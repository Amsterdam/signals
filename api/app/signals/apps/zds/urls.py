from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .api.views import SignalZDSViewSet

# API Version 0
router = DefaultRouter()
router.register(r'signals', SignalZDSViewSet, base_name='zds')


urlpatterns = [
    path('', include((router.urls, 'zds'), namespace='v0')),
]
