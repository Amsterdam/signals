import glob
import os

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from rest_framework import renderers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.api.generics.permissions import SIAPermissions, SIAReportPermissions
from signals.auth.backend import JWTAuthBackend


class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = ''
    format = ''

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class PrivateCsvViewSet(viewsets.ViewSet):
    """
    V1 private ViewSet to retrieve generated csv files
    https://stackoverflow.com/a/51936269
    """

    authentication_classes = (JWTAuthBackend, )
    permission_classes = (SIAPermissions & SIAReportPermissions, )

    @action(methods=['get'], detail=True, renderer_classes=(PassthroughRenderer,))
    def download(self, *args, **kwargs):
        if not settings.DWH_MEDIA_ROOT:
            return self._not_found(msg='Unconfigured Csv location')

        now = timezone.now()
        src_folder = f'{settings.DWH_MEDIA_ROOT}/{now:%Y}/{now:%m}/{now:%d}'

        if not os.path.exists(src_folder):
            return self._not_found(msg='Incorrect Csv folder')

        list_of_files = glob.glob(f'{src_folder}/*.zip', recursive=True)
        latest_file = None if not list_of_files else max(list_of_files, key=os.path.getctime)

        if not latest_file:
            return self._not_found(msg='No Csv files in folder')

        return FileResponse(
            open(latest_file, 'rb'),
            as_attachment=True,
            filename=self._path_leaf(latest_file)
        )

    def _path_leaf(self, path):
        head, tail = os.path.split(path)
        return tail or os.path.basename(head)

    def _not_found(self, msg):
        return Response(
            data={
                'result': msg
            },
            status=status.HTTP_404_NOT_FOUND
        )
