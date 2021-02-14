import base64
import io
import logging
import os

from django.core.files.storage import default_storage
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class DataUriImageEncodeService:
    @staticmethod
    def resize(image, max_size):
        # Consider image orientation:
        if image.width > image.height:
            # landscape
            width = max_size
            height = int((max_size / image.width) * image.height)
        else:
            # portrait
            width = int((max_size / image.height) * image.width)
            height = max_size

        return image.resize(size=(width, height), resample=Image.LANCZOS).convert('RGB')

    @staticmethod
    def get_context_data_images(signal, max_size):
        jpg_data_uris = []
        for att in signal.attachments.all():
            # Attachment is_image property is currently not reliable
            _, ext = os.path.splitext(att.file.name)
            if ext.lower() not in ['.gif', '.jpg', '.jpeg', '.png']:
                continue  # unsupported image format, or not image format

            with io.BytesIO() as buffer:
                try:
                    with default_storage.open(att.file.name) as file:
                        buffer.write(file.read())
                        image = Image.open(buffer)
                except UnidentifiedImageError:
                    # PIL cannot open the attached file it is probably not an image.
                    msg = f'Cannot open image attachment pk={att.pk}'
                    logger.warning(msg)
                    continue
                except:  # noqa:E722
                    # Attachment cannot be opened - log the exception.
                    msg = f'Cannot open image attachment pk={att.pk}'
                    logger.warning(msg, exc_info=True)
                    continue

                if image.width > max_size or image.height > max_size:
                    image = DataUriImageEncodeService.resize(image, max_size)

                with io.BytesIO() as new_buffer:
                    new_buffer = io.BytesIO()
                    image.save(new_buffer, format='JPEG')
                    encoded = f'data:image/jpg;base64,{base64.b64encode(new_buffer.getvalue()).decode("utf-8")}'

            jpg_data_uris.append(encoded)

        return jpg_data_uris
