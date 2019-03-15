from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from signals.apps.users.views import UserMeView

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', include('signals.apps.api.urls')),
    path('signals/user/', include('signals.apps.users.urls')),
    path('signals/admin/', admin.site.urls),

    # DEPRECATED url route for `auth/me`. Should be fixed in the frontend before we can remove
    # this endpoint here.
    path('signals/auth/me/', UserMeView.as_view()),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),

    path('signals/experimental/dashboards/', include('signals.apps.dashboards.urls')),
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
