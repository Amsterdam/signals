# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from io import BytesIO
from struct import error as StructError
from struct import pack

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageCms, ImageOps, PngImagePlugin, UnidentifiedImageError, features

MAX_ICC_BYTES = 1_048_576


class _LimitedBuffer(BytesIO):
    def __init__(self, max_bytes):
        super().__init__()
        self.max_bytes = max_bytes

    def write(self, data):
        if self.tell() + len(data) > self.max_bytes:
            raise ValidationError('Processed image exceeds the attachment size limit.')
        return super().write(data)


def _render_frame(image, image_format):
    frame = ImageOps.exif_transpose(image)
    if (frame.mode == 'P' or image_format == 'GIF'
            or ('transparency' in frame.info and frame.mode != 'I;16')):
        frame = frame.convert('RGBA')

    profile = image.info.get('icc_profile')
    if profile:
        if not features.check_module('littlecms2'):
            raise ValidationError('Image color conversion is unavailable. Please upload another image.')
        if len(profile) > MAX_ICC_BYTES:
            raise ValidationError('Image color profile exceeds the processing limit.')
        output_mode = 'RGBA' if 'A' in frame.getbands() else 'RGB'
        frame = ImageCms.profileToProfile(
            frame, ImageCms.ImageCmsProfile(BytesIO(profile)),
            ImageCms.createProfile('sRGB'), outputMode=output_mode,
        )
    elif image_format == 'JPEG' and frame.mode not in ('RGB', 'L'):
        frame = frame.convert('RGB')

    # A fresh image, not an info-dict blacklist: plugins must never inherit input metadata.
    clean = Image.new(frame.mode, frame.size)
    clean.paste(frame)
    if frame.mode == 'I;16' and 'transparency' in frame.info:
        # Keep the decoded numeric tRNS key; RGBA conversion would clip 16-bit samples to 8 bits.
        clean.info['transparency'] = frame.info['transparency']
    return clean


def _read_frames(image, image_format):
    frames = []
    durations = []
    total_pixels = 0
    for index in range(settings.IMAGE_MAX_FRAMES + 1):
        try:
            image.seek(index)
        except EOFError:
            break
        pixels = image.width * image.height
        total_pixels += pixels
        if (index == settings.IMAGE_MAX_FRAMES or pixels > settings.IMAGE_MAX_FRAME_PIXELS
                or total_pixels > settings.IMAGE_MAX_TOTAL_PIXELS):
            raise ValidationError('Image exceeds the frame or pixel processing limit.')
        image.load()
        frames.append(_render_frame(image, image_format))
        durations.append(image.info.get('duration', 0))
        if image_format == 'JPEG':
            break  # JPEG-compatible MPO/HDR containers keep only the primary, standard-range picture.
    return frames, durations


def _png_rendering_info(info):
    rendering = PngImagePlugin.PngInfo()
    if info.get('icc_profile'):
        rendering.add(b'sRGB', b'\x00')  # Pixels were converted to sRGB; never copy the uploaded profile.
        return rendering
    if 'srgb' in info:
        if info['srgb'] not in range(4):
            raise ValidationError('Invalid PNG rendering intent.')
        rendering.add(b'sRGB', pack('B', info['srgb']))
    if 'gamma' in info:
        rendering.add(b'gAMA', pack('>I', round(info['gamma'] * 100000)))
    if 'chromaticity' in info:
        rendering.add(b'cHRM', pack('>8I', *(round(value * 100000) for value in info['chromaticity'])))
    return rendering


def _encode(image, output):
    image_format = 'JPEG' if image.format == 'MPO' else image.format
    if image_format not in ('JPEG', 'PNG', 'GIF'):
        raise ValidationError('Only JPEG, PNG and GIF images can be processed.')
    default_image = bool(image.info.get('default_image', False))
    loop = image.info.get('loop')
    rendering = _png_rendering_info(image.info) if image_format == 'PNG' else None
    frames, durations = _read_frames(image, image_format)
    options = {}
    if image_format == 'JPEG':
        options.update(quality=95, subsampling=0)
    elif image_format == 'GIF':
        options.update(save_all=True, append_images=frames[1:], duration=durations, disposal=2, optimize=False)
    elif len(frames) > 1:
        options.update(
            save_all=True, append_images=frames[1:], default_image=default_image,
            duration=durations[1:] if default_image else durations, disposal=0, blend=0,
        )
    if rendering is not None:
        options['pnginfo'] = rendering
    if image_format != 'JPEG' and loop is not None:
        options['loop'] = loop
    frames[0].save(output, format=image_format, **options)


def sanitize_image(content, max_bytes):
    """Return a new encoded image; never return the original on processing failure."""
    content.seek(0)
    try:
        if content.size > max_bytes:
            raise ValidationError('Image exceeds the attachment size limit.')
        if min(settings.IMAGE_MAX_FRAMES, settings.IMAGE_MAX_FRAME_PIXELS, settings.IMAGE_MAX_TOTAL_PIXELS) <= 0:
            raise ValidationError('Image processing limits must be positive.')
        # verify() catches structural corruption before a separate, complete pixel decode.
        with Image.open(content, formats=('JPEG', 'PNG', 'GIF')) as image:
            image.verify()
        content.seek(0)
        with Image.open(content, formats=('JPEG', 'PNG', 'GIF')) as image, _LimitedBuffer(max_bytes) as output:
            _encode(image, output)
            return ContentFile(output.getvalue(), name=content.name)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, EOFError, StructError,
            Image.DecompressionBombError, ImageCms.PyCMSError) as exc:
        raise ValidationError('Image could not be processed safely. Please upload another image.') from exc
    finally:
        content.seek(0)
