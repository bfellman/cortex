import json
from datetime import datetime, date

import mongomock
import pytest

from cortex.api import app
USER = {'user_id': '1', 'username': 'Benny', 'gender': 'Male'}
NOW = "2020-06-01"
FEELINGS = {'hunger': 0.5, 'exhaustion': 0.25, 'happiness': 0.75, 'thirst': -0.25}



@pytest.fixture
def setup_api():
        db = mongomock.MongoClient().db
        snapshot = {'datetime': str(int(datetime.fromisoformat(NOW).timestamp())), 'feelings': FEELINGS}
        db.users.update_one({'user_id': '1'}, {'$set': USER}, upsert=True)
        db.snapshots.update_one({'_id':0, 'user_id': '1', 'datetime': snapshot['datetime']}, {'$set': snapshot}, upsert=True)
        app.config['DB'] = db


def test_get_users(setup_api):
        response = app.test_client().get("/users")
        assert (json.loads(response.data)['message'][0] == {'user_id': '1', 'username': 'Benny'})


def test_get_user(setup_api):
        response = app.test_client().get("/users/1")
        assert (json.loads(response.data)['message'] == USER)


def test_get_snapshots(setup_api):
        response = app.test_client().get("/users/1/snapshots")
        timestamp = json.loads(response.data)['message'][0]['datetime']
        assert (date.fromtimestamp(int(timestamp)).isoformat() == NOW)


def test_get_snapshot(setup_api):
        response = app.test_client().get("/users/1/snapshots/0")
        assert json.loads(response.data)['message'] == ['feelings']


def test_get_result(setup_api):
        response = app.test_client().get("/users/1/snapshots/0/feelings")
        assert json.loads(response.data)['message'] == FEELINGS