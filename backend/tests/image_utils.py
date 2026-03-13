from io import BytesIO

from PIL import Image


def tiny_jpeg_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), color=(120, 160, 200)).save(output, format="JPEG", quality=90)
    return output.getvalue()


def tiny_png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGBA", (2, 2), color=(120, 160, 200, 255)).save(output, format="PNG")
    return output.getvalue()
