from rest_framework import routers


class SignalsAPIRootViewVersion1(routers.APIRootView):
    """Signalen API versie 1 (in development)."""

    def get_view_name(self):
        return 'Signals API Version 1'


class SignalsRouterVersion1(routers.DefaultRouter):
    APIRootView = SignalsAPIRootViewVersion1

    # Overriding the `routes` attribute from the default DRF `routes`. We do this to control the
    # usage of trailing slashes for different routes. In DRF you can only add or remove the
    # trailing slash for all routes...
    routes = [
        # List route.
        routers.Route(
            url=r'^{prefix}/$',
            mapping={
                'get': 'list',
                'post': 'create',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        routers.DynamicRoute(
            url=r'^{prefix}/{url_path}$',
            name='{basename}-{url_name}',
            detail=False,
            initkwargs={}
        ),
        # Detail route.
        routers.Route(
            url=r'^{prefix}/{lookup}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        routers.DynamicRoute(
            url=r'^{prefix}/{lookup}/{url_path}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={}
        ),
    ]
