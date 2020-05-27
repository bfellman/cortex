import json


def parse_feelings(data):
    unpacked_data = json.loads(data)
    if 'feelings' in unpacked_data:
        return {'user_id': unpacked_data['user_id'],
                'datetime': unpacked_data['datetime'],
                'feelings': unpacked_data['feelings']}
