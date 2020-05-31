from datetime import date
from pathlib import Path
from PIL import Image

from cortex.client import sample_reader, send_msg_to_server

SAMPLE_PATH = Path(__file__).parent / "inputs" / "3_entries.mind.gz"


def test_user():
    user = next(sample_reader(SAMPLE_PATH))
    assert user.username == "Dan Gittik"
    assert user.user_id == 42
    assert date.fromtimestamp(user.birthday) == date.fromisoformat("1992-03-05")


def test_snapshot():
    it = sample_reader(SAMPLE_PATH)
    next(it)
    snapshot = next(it)

    # check pose
    assert 0.48 < snapshot.pose.translation.x < 0.49
    assert 0.95 < snapshot.pose.rotation.w < 0.96

    # check color image
    size = (snapshot.color_image.height, snapshot.color_image.width)
    assert size == (1080, 1920)
    Image.frombytes(mode='RGB', size=size, data=snapshot.color_image.data)

    # check depth image
    size = (snapshot.depth_image.height, snapshot.depth_image.width)
    assert size == (172, 224)
    assert(len(snapshot.depth_image.data) == size[0] * size[1])

    # check feelings
    snapshot = next(it)
    assert 0.001 < snapshot.feelings.hunger < 0.002
    assert 0.003 < snapshot.feelings.thirst < 0.004
    assert 0.002 < snapshot.feelings.exhaustion < 0.003
    assert snapshot.feelings.happiness == 0


def test_send_message_to_server(httpserver):
    httpserver.expect_request('/gamba', method="POST", data='samal gamba').respond_with_data("ok")
    send_msg_to_server(server_url=httpserver.url_for('/gamba'), msg='samal gamba')