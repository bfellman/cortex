from datetime import date, datetime

import click
import hyperlink
import requests
from flask import json
from tabulate import tabulate

from cortex import cortex_client_pb2


def get_from_server(server_url, msg=""):
    try:
        response = requests.get(server_url, data=msg, timeout=2)
        if response.status_code != requests.codes.ok:
            err_msg = ""
            try:
                err_msg = json.loads(response.text)['message']
            except Exception:
                pass
            exit(f"ERROR: server response code is {response.status_code} {err_msg}")
        return json.loads(response.text)['message']
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
        exit(f"ERROR: couldnt connect to Server at {server_url}, details:\n{e}")


@click.group()
def main():
    pass


@main.command('get-users')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
def get_users(host, port):
    """get all users"""
    req_url = f"http://{host}:{port}/users"
    resp = get_from_server(req_url)
    if resp:
        print(tabulate(resp, headers="keys"))


@main.command('get-user')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
@click.argument('user_id')
def get_user(host, port, user_id):
    """get all info about a specific user (use same id displayed in get-users"""
    req_url = f"http://{host}:{port}/users/{user_id}"
    resp = get_from_server(req_url)
    if resp:
        resp['birthday'] = date.fromtimestamp(resp['birthday']).isoformat()
        print(tabulate([resp], headers="keys"))


@main.command('get-snapshots')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
@click.argument('user_id')
def get_snapshots(host, port, user_id):
    """get list of all snapshots for a specific user"""
    req_url = f"http://{host}:{port}/users/{user_id}/snapshots"
    resp = get_from_server(req_url)
    if resp:
        for r in resp:
            r['datetime'] = datetime.fromtimestamp(int(r['datetime']) / 1000).isoformat()
        print(f"# snapshots for {user_id=}")
        print(tabulate(resp, headers="keys"))


@main.command('get-snapshot')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
@click.argument('user_id')
@click.argument('snapshot_id')
def get_snapshot(host, port, user_id, snapshot_id):
    """get list of all results for a specific snapshot of a speicific user (use same ID as the one printed in get-snapshots"""
    req_url = f"http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}"
    resp = get_from_server(req_url)
    if resp:
        resp_dict = {'results': resp}
        print(f"# results for {user_id=} {snapshot_id=}:")
        print(tabulate(resp_dict, headers="keys"))


@main.command('get-result')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
@click.argument('user_id')
@click.argument('snapshot_id')
@click.argument('result_name')
def get_result(host, port, user_id, snapshot_id, result_name):
    """get detailed result, from the available results presented by get-snapshot"""
    req_url = f"http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}/{result_name}"
    resp = get_from_server(req_url)
    if resp:
        for k, v in resp.items():
            if isinstance(v, str) and hyperlink.parse(v).scheme == "http":
                resp[k] = hyperlink.parse(v).to_text()
        print(f"# {result_name} for {user_id=} {snapshot_id=}:")
        print(tabulate([resp], headers="keys"))


if __name__ == "__main__":
    main()
