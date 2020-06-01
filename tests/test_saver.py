import json
from datetime import datetime
from click.testing import CliRunner
from cortex import saver


def test_add_feelings(tmpdir):
    db_url = "mockmongo://127.0.0.1:9119"
    user_msg = {'user_id': '1', 'username': 'Benny', 'gender': 'Male', 'msg_type': 'user'}
    feelings = {'hunger': 0.5, 'exhaustion': 0.25, 'happiness': 0.75, 'thirst': -0.25}
    now = "2020-06-01"
    feelings_msg = {'user_id': '1', 'datetime': str(int(datetime.fromisoformat(now).timestamp())), 'feelings': feelings}
    feelings_file = tmpdir/'feelings'
    with open(feelings_file, 'w') as fh:
        json.dump(feelings_msg, fh)
    runner = CliRunner()
    res = runner.invoke(saver.saver_cli, f"-d {db_url} feelings {feelings_file}")
    assert not res.exception
    saver.Saver(db_url).handle_snapshot(json.dumps(user_msg))


def test_run_saver():
    runner = CliRunner()
    res = runner.invoke(saver.run_saver_cli, 'mockmongo://127.0.0.1:9119 rabbitmq://127.0.0.1:8888/'.split())
    assert res.exception and "can't connect to message queue" in res.output