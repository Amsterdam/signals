import base64
import io
import logging
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from PIL import Image, UnidentifiedImageError

from signals.apps.api.generics.permissions import SIAPermissions, SignalViewObjectPermission
from signals.apps.api.pdf.views import PDFTemplateView  # TODO: move these
from signals.apps.signals.models import Signal
from signals.apps.signals.utils.map import MapGenerator
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


def _get_data_uri(static_file):
    formats = {
        '.svg': 'data:image/svg+xml;base64,',
        '.jpg': 'data:image/jpeg;base64',
        '.png': 'data:image/png;base64,',
    }

    if not static_file:  # protect against None or ''
        return ''

    try:
        result = finders.find(static_file)
    except SuspiciousFileOperation:  # when file path starts with /
        return ''

    if result:
        _, ext = os.path.splitext(result)
        if not ext:
            return ''

        try:
            start = formats[ext]
        except KeyError:
            return ''  # We want no HTTP 500, just a missing image

        with open(result, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        data_uri = start + encoded

        return data_uri
    else:
        return ''  # missing static file, results in missing image


class GeneratePdfView(SingleObjectMixin, PDFTemplateView):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)
    object_permission_classes = (SignalViewObjectPermission, )
    pagination_class = None
    map_generator = MapGenerator()

    queryset = Signal.objects.all()

    template_name = 'api/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    max_size = settings.API_PDF_RESIZE_IMAGES_TO

    def check_object_permissions(self, request, obj):
        for permission_class in self.object_permission_classes:
            permission = permission_class()
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(request=self.request, obj=obj)
        return obj

    def _resize(self, image):
        # Consider image orientation:
        if image.width > image.height:
            # landscape
            width = self.max_size
            height = int((self.max_size / image.width) * image.height)
        else:
            # portrait
            width = int((self.max_size / image.height) * image.width)
            height = self.max_size

        return image.resize(size=(width, height), resample=Image.LANCZOS).convert('RGB')

    def _get_context_data_images(self, signal):
        jpg_data_urls = []
        for att in signal.attachments.all():
            # Attachment is_image property is currently not reliable
            _, ext = os.path.splitext(att.file.name)
            if ext not in ['.gif', '.jpg', '.jpeg', '.png']:
                continue  # unsupported image format, or not image format

            # Since we want a PDF to be output, we catch, log and ignore errors
            # while opening attachments. A missing image is not as bad as a
            # complete failure to render the requested PDF.
            try:
                with default_storage.open(att.file.name) as file:
                    buffer = io.BytesIO(file.read())
                image = Image.open(buffer)
            except UnidentifiedImageError:
                # PIL cannot open the attached file it is probably not an image.
                msg = f'Cannot open image attachment pk={att.pk}'
                logger.warn(msg)
                continue
            except:  # noqa:E722
                # Attachment cannot be opened - log the exception.
                msg = f'Cannot open image attachment pk={att.pk}'
                logger.warn(msg, exc_info=True)
                continue

            if image.width > self.max_size or image.height > self.max_size:
                image = self._resize(image)

            new_buffer = io.BytesIO()
            image.save(new_buffer, format='JPEG')
            encoded = f'data:image/jpg;base64,{base64.b64encode(new_buffer.getvalue()).decode("utf-8")}'

            jpg_data_urls.append(encoded)

        return jpg_data_urls

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        logo_src = _get_data_uri(settings.API_PDF_LOGO_STATIC_FILE)
        img_data_uri = None
        bbox = None

        if settings.DEFAULT_MAP_TILE_SERVER:
            map_img = self.map_generator.make_map(
                url_template=settings.DEFAULT_MAP_TILE_SERVER,
                lat=self.object.location.geometrie.coords[1],
                lon=self.object.location.geometrie.coords[0],
                zoom=17,
                img_size=[680, 250]
            )
            # transform image to png -> bytes -> data uri
            png_array = io.BytesIO()
            map_img.save(png_array, format='png')
            encoded = base64.b64encode(png_array.getvalue()).decode()
            img_data_uri = 'data:image/png;base64,{}'.format(encoded)
        else:
            rd_coordinates = self.object.location.get_rd_coordinates()
            bbox = '{},{},{},{}'.format(
                rd_coordinates.x - 340.00,
                rd_coordinates.y - 125.00,
                rd_coordinates.x + 340.00,
                rd_coordinates.y + 125.00,
            )
        jpg_data_urls = self._get_context_data_images(self.object)

        return super(GeneratePdfView, self).get_context_data(
            bbox=bbox,
            img_data_uri=img_data_uri,
            jpg_data_urls=jpg_data_urls,
            user=self.request.user,
            logo_src=logo_src,
        )
