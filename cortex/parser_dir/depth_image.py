import json
import tempfile
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def parse_depth_image(data):
    unpacked_data = json.loads(data)
    if 'depth_image' in unpacked_data:
        try:
            depth_image_dict = unpacked_data['depth_image']
            res = dict()
            bin_path = depth_image_dict['path']
            size = depth_image_dict['height'], depth_image_dict['width']
            img_1d_array = np.load(bin_path)
            img_array = np.reshape(img_1d_array, size)
            plt.imshow(img_array, cmap='hot', interpolation='nearest')
            image_path = Path(tempfile.mkdtemp()) / 'depth_image.png'
            plt.savefig(image_path)
            res['path'] = str(image_path)
            res['size'] = f"{size[0]}x{size[1]}"
            return {'user_id': unpacked_data['user_id'],
                    'datetime': unpacked_data['datetime'],
                    'depth_image': res}
        except Exception as e:
            exit(f"ERROR: couldn't parse image\n{e}")
