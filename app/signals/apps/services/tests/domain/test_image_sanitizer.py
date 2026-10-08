# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from io import BytesIO
from random import Random
from struct import pack
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.test import override_settings
from PIL import Image, ImageCms, IptcImagePlugin, PngImagePlugin

from signals.apps.services.domain.image_sanitizer import sanitize_image

LIMIT = 20 * 1024 * 1024
MARKER = b'SYNTHETIC-PRIVATE-METADATA'


def image_upload(image_format='JPEG', **options):
    image = Image.new('RGB', (12, 8), 'red')
    output = BytesIO()
    image.save(output, format=image_format, **options)
    return ContentFile(output.getvalue(), name=f'synthetic.{image_format.lower()}')


@pytest.mark.parametrize('image_format', ['JPEG', 'PNG', 'GIF'])
def test_removes_metadata_and_trailing_payload(image_format):
    options = {}
    if image_format in ('JPEG', 'PNG'):
        exif = Image.Exif()
        exif[271] = MARKER.decode()
        exif[36867] = '2000:01:02 03:04:05'
        exif[34853] = {1: 'N', 2: (1.0, 2.0, 3.0), 3: 'E', 4: (4.0, 5.0, 6.0)}
        options['exif'] = exif
    if image_format == 'PNG':
        info = PngImagePlugin.PngInfo()
        info.add_text('Comment', MARKER.decode())
        info.add_text('Description', MARKER.decode(), zip=True)
        info.add_itxt('XML:com.adobe.xmp', MARKER.decode())
        options['pnginfo'] = info
    else:
        options['comment'] = MARKER
    content = image_upload(image_format, **options)
    content.seek(0, 2)
    content.write(b'MOTION-PHOTO-PAYLOAD' + MARKER)
    content.seek(0)
    assert MARKER in content.read()

    clean = sanitize_image(content, LIMIT)

    assert MARKER not in clean.read()
    with Image.open(clean) as image:
        image.load()
        assert not image.getexif()
        assert not {'exif', 'comment', 'xmp', 'icc_profile', 'XML:com.adobe.xmp'} & image.info.keys()
        assert image.size == (12, 8)
        assert image.format == image_format
    assert content.tell() == 0


@pytest.mark.parametrize('orientation', range(2, 9))
def test_applies_orientation(orientation):
    image = Image.new('RGB', (3, 2))
    image.putdata([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)])
    exif = Image.Exif()
    exif[274] = orientation
    output = BytesIO()
    image.save(output, format='PNG', exif=exif)
    transpose = {
        2: Image.Transpose.FLIP_LEFT_RIGHT, 3: Image.Transpose.ROTATE_180,
        4: Image.Transpose.FLIP_TOP_BOTTOM, 5: Image.Transpose.TRANSPOSE,
        6: Image.Transpose.ROTATE_270, 7: Image.Transpose.TRANSVERSE, 8: Image.Transpose.ROTATE_90,
    }
    clean = sanitize_image(ContentFile(output.getvalue(), name='orientation.png'), LIMIT)
    with Image.open(clean) as result:
        expected = image.transpose(transpose[orientation])
        assert result.size == expected.size
        assert result.tobytes() == expected.tobytes()
        assert not result.getexif()


@pytest.mark.parametrize('mode', ['RGBA', 'LA', 'P', 'I;16'])
def test_png_preserves_pixels_and_transparency(mode):
    image = Image.new(mode, (4, 3))
    if mode == 'P':
        image.putpalette([255, 0, 0, 0, 255, 0] + [0] * 762)
        image.putpixel((1, 1), 1)
        image.info['transparency'] = 0
    elif mode == 'I;16':
        image.putpixel((1, 1), 40000)
    else:
        image.putpixel((1, 1), (20, 40, 60, 128) if mode == 'RGBA' else (20, 128))
    output = BytesIO()
    image.save(output, format='PNG')
    clean = sanitize_image(ContentFile(output.getvalue(), name='transparent.png'), LIMIT)
    with Image.open(clean) as result:
        if mode == 'I;16':
            assert result.getpixel((1, 1)) == 40000
        else:
            assert result.convert('RGBA').tobytes() == image.convert('RGBA').tobytes()


def test_png_preserves_16bit_transparency_key_without_clipping():
    image = Image.new('I;16', (2, 1))
    image.putpixel((0, 0), 40000)
    image.putpixel((1, 0), 45000)
    output = BytesIO()
    image.save(output, format='PNG', transparency=40000)
    clean = sanitize_image(ContentFile(output.getvalue(), name='transparent16.png'), LIMIT)
    with Image.open(clean) as result:
        assert result.mode == 'I;16'
        assert result.tobytes() == image.tobytes()
        assert result.info['transparency'] == 40000


def test_converts_icc_without_retaining_profile():
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    # A valid profile can have trailing opaque content. No input ICC bytes are copied.
    content = image_upload('PNG', icc_profile=profile + MARKER)
    clean = sanitize_image(content, LIMIT)
    assert MARKER not in clean.read()
    with Image.open(clean) as result:
        assert 'icc_profile' not in result.info
        assert result.getpixel((0, 0)) == (255, 0, 0)


@pytest.mark.parametrize('profile', [b'invalid-profile', b'x' * (1024 * 1024 + 1)], ids=['invalid', 'oversized'])
def test_rejects_bad_icc(profile):
    with pytest.raises(ValidationError):
        sanitize_image(image_upload('PNG', icc_profile=profile), LIMIT)


@pytest.mark.parametrize('image_format', ['GIF', 'PNG'])
@pytest.mark.parametrize('disposal', [1, 2, 3])
def test_preserves_composited_animation(image_format, disposal):
    frames = [Image.new('RGBA', (6, 4), (0, 0, 0, 0)) for _ in range(3)]
    for index, frame in enumerate(frames):
        frame.putpixel((index, 1), (255, 0, 0, 255))
    output = BytesIO()
    frames[0].save(
        output, format=image_format, save_all=True, append_images=frames[1:],
        duration=[100, 200, 300], loop=2,
        disposal=disposal if image_format == 'GIF' else disposal - 1,
        comment=MARKER,
    )
    content = ContentFile(output.getvalue(), name=f'animation.{image_format.lower()}')
    clean = sanitize_image(content, LIMIT)
    assert MARKER not in clean.read()
    with Image.open(content) as original, Image.open(clean) as result:
        assert result.n_frames == original.n_frames
        assert result.info['loop'] == 2
        for index in range(original.n_frames):
            original.seek(index)
            result.seek(index)
            assert result.info['duration'] == original.info['duration']
            assert result.convert('RGBA').tobytes() == original.convert('RGBA').tobytes()


def test_apng_default_image_is_not_an_animation_frame():
    content = BytesIO()
    frames = [Image.new('RGBA', (3, 2), color) for color in ('red', 'green', 'blue')]
    frames[0].save(
        content, format='PNG', save_all=True, append_images=frames[1:],
        default_image=True, duration=[100, 200], loop=0,
    )
    clean = sanitize_image(ContentFile(content.getvalue(), name='default.png'), LIMIT)
    with Image.open(clean) as image:
        assert image.info['default_image'] is True
        assert image.n_frames == 3
        image.seek(1)
        assert image.info['duration'] == 100
        assert image.getpixel((0, 0)) == (0, 128, 0, 255)


@pytest.mark.parametrize('data', [b'not an image', b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n'])
def test_rejects_invalid_images(data):
    with pytest.raises(ValidationError):
        sanitize_image(ContentFile(data, name='broken.jpg'), LIMIT)


def test_rejects_truncated_jpeg():
    content = image_upload()
    with pytest.raises(ValidationError):
        sanitize_image(ContentFile(content.read()[:-20], name='truncated.jpg'), LIMIT)


@pytest.mark.parametrize('limit_name', ['IMAGE_MAX_FRAME_PIXELS', 'IMAGE_MAX_TOTAL_PIXELS', 'IMAGE_MAX_FRAMES'])
def test_processing_limits(limit_name):
    with override_settings(**{limit_name: 0}), pytest.raises(ValidationError):
        sanitize_image(image_upload(), LIMIT)


def test_input_size_limit():
    with pytest.raises(ValidationError):
        sanitize_image(image_upload(), 10)


def test_output_size_limit():
    output = BytesIO()
    image = Image.frombytes('RGB', (64, 64), Random(0).randbytes(64 * 64 * 3))
    image.save(output, format='JPEG', quality=1)
    content = ContentFile(output.getvalue(), name='size.jpg')
    with pytest.raises(ValidationError, match='Processed image'):
        sanitize_image(content, content.size)


def test_encoder_failure_is_not_an_original_file_fallback():
    content = image_upload()
    with patch('PIL.Image.Image.save', side_effect=OSError('synthetic encoder failure')):
        with pytest.raises(ValidationError):
            sanitize_image(content, LIMIT)


def test_preserves_only_allowlisted_png_rendering_chunks():
    info = PngImagePlugin.PngInfo()
    info.add(b'gAMA', pack('>I', 45455))
    info.add(b'cHRM', pack('>8I', 31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000))
    info.add(b'sRGB', b'\x01')
    info.add_text('Description', MARKER.decode())
    content = image_upload('PNG', pnginfo=info)
    clean = sanitize_image(content, LIMIT)
    with Image.open(content) as original, Image.open(clean) as result:
        assert result.info == {key: original.info[key] for key in ('gamma', 'chromaticity', 'srgb')}


def test_jpeg_xmp_and_iptc_are_removed():
    xmp = b'http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta>' + MARKER + b'</x:xmpmeta>'
    iptc = b'\x1c\x02\x78' + pack('>H', len(MARKER)) + MARKER
    photoshop = b'Photoshop 3.0\x00' + b'8BIM\x04\x04\x00\x00' + pack('>I', len(iptc)) + iptc
    photoshop += b'\x00' if len(iptc) % 2 else b''
    jpeg = image_upload().read()
    data = (jpeg[:2] + b'\xff\xe1' + pack('>H', len(xmp) + 2) + xmp
            + b'\xff\xed' + pack('>H', len(photoshop) + 2) + photoshop + jpeg[2:])
    content = ContentFile(data, name='metadata.jpg')
    with Image.open(content) as original:
        assert IptcImagePlugin.getiptcinfo(original)[(2, 120)] == MARKER
        assert MARKER in original.info['xmp']
    clean = sanitize_image(content, LIMIT)
    assert MARKER not in clean.read()
    with Image.open(clean) as result:
        assert IptcImagePlugin.getiptcinfo(result) is None
        assert 'xmp' not in result.info


@pytest.mark.parametrize('settings_override', [
    {'IMAGE_MAX_FRAMES': 2},
    {'IMAGE_MAX_TOTAL_PIXELS': 60},
])
def test_animation_budget_is_cumulative(settings_override):
    output = BytesIO()
    frames = [Image.new('RGB', (6, 4), color) for color in ('red', 'green', 'blue')]
    frames[0].save(output, format='GIF', save_all=True, append_images=frames[1:])
    with override_settings(**settings_override), pytest.raises(ValidationError, match='processing limit'):
        sanitize_image(ContentFile(output.getvalue(), name='frames.gif'), LIMIT)


def test_size_rejection_precedes_image_open_and_rewinds_input():
    content = image_upload()
    content.seek(12)
    with patch('signals.apps.services.domain.image_sanitizer.Image.open') as image_open:
        with pytest.raises(ValidationError, match='attachment size'):
            sanitize_image(content, content.size - 1)
    image_open.assert_not_called()
    assert content.tell() == 0
    assert not content.closed


def test_decompression_bomb_is_rejected():
    with patch.object(Image, 'MAX_IMAGE_PIXELS', 10), pytest.raises(ValidationError):
        sanitize_image(image_upload(), LIMIT)


def test_negative_frame_limit_is_a_validation_error():
    with override_settings(IMAGE_MAX_FRAMES=-1), pytest.raises(ValidationError, match='positive'):
        sanitize_image(image_upload(), LIMIT)


def test_frame_limit_rejects_before_loading_pixels():
    content = image_upload()
    with override_settings(IMAGE_MAX_FRAME_PIXELS=95):
        with patch('PIL.JpegImagePlugin.JpegImageFile.load') as load:
            with pytest.raises(ValidationError, match='processing limit'):
                sanitize_image(content, LIMIT)
        load.assert_not_called()


def test_temporary_upload_remains_open_and_reusable():
    data = image_upload('PNG').read()
    with TemporaryUploadedFile('temporary.png', 'image/png', len(data), None) as content:
        content.write(data)
        clean = sanitize_image(content, LIMIT)
        assert not content.closed
        assert content.tell() == 0
        assert content.read() == data
        assert clean.size


def test_png_crc_corruption_is_rejected():
    data = bytearray(image_upload('PNG').read())
    idat = data.index(b'IDAT')
    data[idat + 4] ^= 1
    with pytest.raises(ValidationError):
        sanitize_image(ContentFile(bytes(data), name='crc.png'), LIMIT)


def test_missing_color_engine_rejects_profiled_upload():
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    content = image_upload('PNG', icc_profile=profile)
    with patch('signals.apps.services.domain.image_sanitizer.features.check_module', return_value=False):
        with pytest.raises(ValidationError, match='color conversion'):
            sanitize_image(content, LIMIT)


def test_icc_conversion_preserves_alpha():
    source = Image.new('RGBA', (4, 3), (80, 120, 160, 128))
    output = BytesIO()
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    source.save(output, format='PNG', icc_profile=profile)
    clean = sanitize_image(ContentFile(output.getvalue(), name='alpha.png'), LIMIT)
    with Image.open(clean) as result:
        assert result.tobytes() == source.tobytes()
        assert result.info == {'srgb': 0}


def test_unprofiled_cmyk_jpeg_is_converted_to_rgb():
    output = BytesIO()
    Image.new('CMYK', (6, 4), (0, 128, 128, 0)).save(output, format='JPEG')
    clean = sanitize_image(ContentFile(output.getvalue(), name='cmyk.jpg'), LIMIT)
    with Image.open(clean) as result:
        assert result.mode == 'RGB'
        assert result.size == (6, 4)
        assert all(abs(actual - expected) <= 2 for actual, expected in zip(
            result.getpixel((0, 0)), (255, 127, 127),
        ))
        assert 'icc_profile' not in result.info


def test_mpo_keeps_only_primary_jpeg():
    output = BytesIO()
    Image.new('RGB', (6, 4), 'red').save(
        output, format='MPO', save_all=True, append_images=[Image.new('RGB', (6, 4), 'blue')],
    )
    content = ContentFile(output.getvalue(), name='motion.jpg')
    with Image.open(content) as source:
        assert source.n_frames == 2
    clean = sanitize_image(content, LIMIT)
    with Image.open(clean) as result:
        assert result.format == 'JPEG'
        assert 'mp' not in result.info
        assert result.getpixel((0, 0))[0] > 240


def test_jpeg_embedded_thumbnail_is_discarded():
    thumbnail = image_upload('JPEG', comment=MARKER).read()
    # Minimal little-endian EXIF: empty IFD0 points to a JPEG thumbnail in IFD1.
    tiff = b'II' + pack('<HI', 42, 8) + pack('<HI', 0, 14)
    tiff += pack('<H', 3)
    tiff += pack('<HHII', 259, 3, 1, 6)
    tiff += pack('<HHII', 513, 4, 1, 56)
    tiff += pack('<HHII', 514, 4, 1, len(thumbnail))
    tiff += pack('<I', 0) + thumbnail
    content = image_upload('JPEG', exif=b'Exif\x00\x00' + tiff)
    assert MARKER in content.read()
    clean = sanitize_image(content, LIMIT)
    assert MARKER not in clean.read()
    with Image.open(clean) as result:
        assert not result.getexif()
