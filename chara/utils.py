from PIL import Image, ImageOps
from io import BytesIO


def process_avatar(file):
    image = Image.open(file)

    if image.mode == 'P':
        image = image.convert('RGBA')

    if image.mode == 'RGBA':
        image.load()
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    image.thumbnail((250, 250))
    image = ImageOps.pad(image, (250, 250))

    fo = BytesIO()
    image.save(fo, format='JPEG')
    fo.seek(0)

    return fo
