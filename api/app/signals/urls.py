from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from signals.apps.users.views import UserMeView

schema_view = get_schema_view(
    openapi.Info(
        title='Signals API',
        default_version='v1',
        description='Signals in Amsterdam',
        terms_of_service='https://data.amsterdam.nl/',
        contact=openapi.Contact(email='datapunt@amsterdam.nl'),
        license=openapi.License(name='CC0 1.0 Universal'),
    ),
    validators=['flex', 'ssv'],
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', include('signals.apps.signals.urls')),
    path('signals/user/', include('signals.apps.users.urls')),
    path('signals/admin/', admin.site.urls),

    # DEPRECATED url route for `auth/me`. Should be fixed in the frontend before we can remove
    # this endpoint here.
    path('signals/auth/me/', UserMeView.as_view()),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),

    # Swagger
    url(r'^signals/swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=None),
        name='schema-json'),
    url(r'^signals/swagger/$',
        schema_view.with_ui('swagger', cache_timeout=None),
        name='schema-swagger-ui'),
    url(r'^signals/redoc/$',
        schema_view.with_ui('redoc', cache_timeout=None),
        name='schema-redoc'),
]

if 'signals.apps.zds' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('zds/', include(('signals.apps.zds.urls', 'zds'), namespace="zds")),
    ]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    media_root = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + media_root
