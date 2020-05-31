import json
from pathlib import Path
from datetime import datetime

import pytest
import numpy as np

import cortex.parsers
from cortex.parser_dir import pose, depth_image, color_image
from cortex.parser_dir import feelings


def test_parser(tmpdir):
    old_dir = cortex.parsers.PARSER_DIR
    cortex.parsers.PARSER_DIR = Path(tmpdir)
    tmp_parser = tmpdir / "dump_parser.py"
    tmp_parser.write_text("""
import json
def parse_dumb(data):
    unpacked_data = json.loads(data)
    dumb_data = dict()
    for k,v in unpacked_data.items():
        dumb_data['dumb_' + k] = v
    return dumb_data
    """, encoding=None)
    res = cortex.parsers.parse('dumb', json.dumps({'starbucks': 20}))
    assert res['dumb_starbucks'] == 20
    cortex.parsers.PARSER_DIR = old_dir


def test_run_parser_server():
    with pytest.raises(SystemExit, match=r".* can't connect to message queue.*"):
        cortex.parsers.run_parser_server('rabbitmq://127.0.0.1:8888/', 'pose')



# test specific parsers:
@pytest.fixture(scope="session")
def get_snapshot_dict(tmpdir_factory):
    depth_image_path = tmpdir_factory.mktemp('data').join('depth_image.npy')
    with open(depth_image_path, 'wb') as f:
        np.save(f, np.random.rand(80 * 20))

    color_image_path = tmpdir_factory.mktemp('data').join('color_image')
    with open(color_image_path, 'wb') as f:
        f.write(np.random.randint(0,255,(100,100,3)))
    snapshot = {'datetime': int(datetime.fromisoformat("2020-05-31T21:54:29.123").timestamp()*1000),
                 'user_id': 1,
                 'pose': {'translation': 100, 'rotation': 20},
                 'feelings': {'hunger': 0.5, 'exhaustion':1, 'happiness': -1, 'thirst': 0},
                 'depth_image': {'width': 20, 'height': 80, 'path': str(depth_image_path)},
                 'color_image': {'width': 100, 'height': 100, 'path': str(color_image_path)}
    }
    return json.dumps(snapshot)


def test_parse_pose(get_snapshot_dict):
    res = pose.parse_pose(get_snapshot_dict)
    assert len(res) == 3
    assert res['pose']['rotation'] == 20


def test_parse_feelings(get_snapshot_dict):
    res = feelings.parse_feelings(get_snapshot_dict)
    assert len(res) == 3
    assert res['feelings']['exhaustion'] == 1


def test_parse_depth_image(get_snapshot_dict):
    res = depth_image.parse_depth_image(get_snapshot_dict)
    assert len(res) == 3
    assert Path(res['depth_image']['path']).exists()


def test_parse_color_image(get_snapshot_dict):
    res = color_image.parse_color_image(get_snapshot_dict)
    assert len(res) == 3
    assert Path(res['color_image']['path']).exists()



