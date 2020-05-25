import json


def parse_pose(data):
    unpacked_data = json.loads(data)
    if 'pose' in unpacked_data:
        return {'user_id': unpacked_data['user_id'],
                'datetime': unpacked_data['datetime'],
                'pose': unpacked_data['pose']}
