from datetime import datetime

from cortex import cli
from click.testing import CliRunner

USER_ID = 13479211987
def test_get_users(httpserver):
    httpserver.expect_request("/users", method="GET").respond_with_json({'message': [{'username': 'Benny',
                                                                                      'user_id': USER_ID},
                                                                                     {'username': 'Covid',
                                                                                      'user_id': 19}
                                                                                     ]})
    runner = CliRunner()
    res = runner.invoke(cli.get_users, f'--host {httpserver.host} --port {httpserver.port}'.split())
    assert 'Benny' in res.output
    assert str(USER_ID) in res.output


def test_get_user(httpserver):
    my_birthday = '1987-11-14'
    httpserver.expect_request(f"/users/{USER_ID}", method="GET").respond_with_json({'message': {'username': 'Benny',
                                                                                     'user_id': USER_ID,
                                                                                     'birthday': datetime.fromisoformat(my_birthday).timestamp()}})
    runner = CliRunner()
    res = runner.invoke(cli.get_user, f'--host {httpserver.host} --port {httpserver.port} {USER_ID}'.split())
    assert 'Benny' in res.output
    assert my_birthday in res.output


def test_get_snapshots(httpserver):
    time_1 = "2020-06-01T17:37:13.288"
    time_2 = "2020-06-01T17:37:54.925"
    httpserver.expect_request(f"/users/{USER_ID}/snapshots", method="GET").respond_with_json(
        {'message': [{'id': 1, 'datetime': int(datetime.fromisoformat(time_1).timestamp()*1000)},
                     {'id': 2, 'datetime': int(datetime.fromisoformat(time_2).timestamp()*1000)}]})
    runner = CliRunner()
    res = runner.invoke(cli.get_snapshots, f'--host {httpserver.host} --port {httpserver.port} {USER_ID}'.split())
    assert time_2 in res.output


def test_get_snapshot(httpserver):
    httpserver.expect_request(f"/users/{USER_ID}/snapshots/101", method="GET").respond_with_json(
        {'message': ['actually', 'any', 'list', 'will do']})
    runner = CliRunner()
    res = runner.invoke(cli.get_snapshot, f'--host {httpserver.host} --port {httpserver.port} {USER_ID} 101'.split())
    assert 'will do' in res.output


def test_get_result(httpserver):
    httpserver.expect_request(f"/users/{USER_ID}/snapshots/101/lunch", method="GET").respond_with_json(
        {'message': {'source': 'moses', 'main': 'burger', 'satisfaction': '504.358'}})
    runner = CliRunner()
    res = runner.invoke(cli.get_result, f'--host {httpserver.host} --port {httpserver.port} {USER_ID} 101 lunch'.split())
    assert '504.358' in res.output

