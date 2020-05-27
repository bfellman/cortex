import json
import tempfile
from pathlib import Path
from PIL import Image as PIL


def parse_color_image(data):
    unpacked_data = json.loads(data)
    image_path = Path(tempfile.mkdtemp()) / 'color_image.jpeg'
    if 'color_image' in unpacked_data:
        try:
            color_image_dict = unpacked_data['color_image']
            res = dict()
            bin_path = color_image_dict['path']
            size = color_image_dict['width'], color_image_dict['height']
            image = PIL.frombytes(mode='RGB', size=size, data=open(bin_path, 'rb').read())
            image.save(image_path)
            res['path'] = str(image_path)
            res['size'] = f"{size[0]}x{size[1]}"
            return {'user_id': unpacked_data['user_id'],
                    'datetime': unpacked_data['datetime'],
                    'color_image': res}
        except Exception as e:
            exit(f"ERROR: couldn't parse image\n{e}")
