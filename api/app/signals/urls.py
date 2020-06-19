from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from signals.apps.graphql.views import SIAGraphQLView

# from signals.apps.users.v0.views import UserMeView

urlpatterns = [
    path('status/', include('signals.apps.health.urls')),

    # The Signals application is routed behind the HAproxy with `/signals/` as path.
    path('signals/', include('signals.apps.api.urls')),
    path('signals/admin/', admin.site.urls),

    # Disbaled V0
    # DEPRECATED url route for `auth/me`. Should be fixed in the frontend before we can remove
    # this endpoint here.
    # path('signals/auth/me/', UserMeView.as_view()),
    # path('signals/user/auth/me/', UserMeView.as_view()),

    # SOAP stand-in endpoints
    path('signals/sigmax/', include('signals.apps.sigmax.urls')),

    # path('signals/experimental/reporting/', include('signals.apps.reporting.urls'))

    # GraphQL endpoint
    path('signals/graphql', csrf_exempt(SIAGraphQLView.as_view(graphiql=True))),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    media_root = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + media_root
