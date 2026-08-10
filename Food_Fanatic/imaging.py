"""Downscale and re-encode uploaded images before they reach storage.

Menu photography arrives straight from a camera or stock library at several
thousand pixels wide, but the largest card that displays it is a few hundred
pixels. Storing the original means every visitor downloads megabytes to render a
thumbnail, so images are resized and re-encoded on the way in.
"""

from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile

# Formats that survive a round trip without changing the file extension. The
# stored name is chosen before the file is written, so re-encoding into a
# different container would leave the name lying about the contents.
RECOMPRESSIBLE_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})


def _measure(content):
    content.seek(0, 2)
    size = content.tell()
    content.seek(0)
    return size


def compress_image(content, max_width=None, quality=None):
    """Return a smaller version of ``content``, or None to store it unchanged.

    None is returned for anything that is not a recompressible image and for
    images that would not get smaller, so the caller can always fall back to the
    original file.
    """
    from PIL import Image, ImageOps

    max_width = max_width or getattr(settings, "IMAGE_MAX_WIDTH", 1200)
    quality = quality or getattr(settings, "IMAGE_QUALITY", 82)

    original_size = _measure(content)
    try:
        image = Image.open(content)
        image.load()
    except Exception:
        # Not an image, or one Pillow cannot decode. Store the upload as it is.
        content.seek(0)
        return None

    image_format = (image.format or "").upper()
    if image_format not in RECOMPRESSIBLE_FORMATS:
        content.seek(0)
        return None

    # Apply the EXIF rotation before it is dropped along with the rest of the
    # metadata, otherwise phone photos come out sideways.
    image = ImageOps.exif_transpose(image)

    if image.width > max_width:
        height = max(1, round(image.height * max_width / image.width))
        image = image.resize((max_width, height), Image.LANCZOS)

    buffer = BytesIO()
    options = {"optimize": True}
    if image_format == "JPEG":
        if image.mode != "RGB":
            image = image.convert("RGB")
        options.update(quality=quality, progressive=True)
    elif image_format == "WEBP":
        options.update(quality=quality, method=6)

    try:
        image.save(buffer, format=image_format, **options)
    except OSError:
        content.seek(0)
        return None
    finally:
        image.close()

    content.seek(0)
    if buffer.tell() >= original_size:
        # Already well optimised; rewriting it would only lose quality.
        return None
    return ContentFile(buffer.getvalue())
