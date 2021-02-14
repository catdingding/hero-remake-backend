from PIL import Image, ImageOps
from io import BytesIO


def process_avatar(file):
    image = Image.open(file)
    image.thumbnail((250, 250))
    image = ImageOps.pad(image, (250, 250))

    fo = BytesIO()
    image.save(fo, format='JPEG')
    fo.seek(0)

    return fo
