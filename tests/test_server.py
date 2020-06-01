import json
from datetime import datetime
import pytest
from google.protobuf.json_format import MessageToDict

from cortex.server import app
from cortex import cortex_client_pb2


class Publisher:
    def __init__(self):
        self.data = ""

    def publish(self, data):
        self.data += data

@pytest.fixture
def get_user():
    user = cortex_client_pb2.User()
    user.username = "Benny"
    user.gender = cortex_client_pb2.User.Gender.MALE
    user.user_id = 1
    user.birthday = int(datetime.fromisoformat("1987-11-14").timestamp())
    return user


@pytest.fixture
def get_snapshot():
    snapshot = cortex_client_pb2.Snapshot()
    snapshot.datetime = int(datetime.fromisoformat("2020-05-31T20:50:23.988").timestamp()*1000)
    snapshot.feelings.hunger = 0.5
    snapshot.feelings.exhaustion = 0.25
    snapshot.feelings.happiness = 0.75
    snapshot.feelings.thirst = -0.25
    return snapshot


def assert_and_del(test_dict, key_values):
    for k, v in key_values:
        assert test_dict[k] == v
        del test_dict[k]


def test_user(get_user):
    p = Publisher()
    app.config['PUBLISH'] = p.publish
    response = app.test_client().post("/user", data=get_user.SerializeToString())
    assert response.status_code == 200
    msg_dict = json.loads(p.data)
    assert_and_del(msg_dict, [('msg_type', 'user'), ('gender', 'MALE')])
    user_dict = MessageToDict(get_user, preserving_proto_field_name=True)
    assert user_dict == msg_dict


def test_snapshot(get_snapshot):

    p = Publisher()
    app.config['PUBLISH'] = p.publish
    response = app.test_client().post("/snapshot/1", data=get_snapshot.SerializeToString())
    assert response.status_code == 200
    msg_dict = json.loads(p.data)
    assert_and_del(msg_dict, [('msg_type', 'snapshot'), ('user_id', "1")])
    snapshot_dict = MessageToDict(get_snapshot, preserving_proto_field_name=True)
    assert snapshot_dict == msg_dict


