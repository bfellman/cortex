import gzip
import struct
import time
from pprint import pprint

import requests
import sys

import click
from flask import json
from tabulate import tabulate

from cortex import cortex_client_pb2
from cortex import cortex_sample_pb2
from urllib.parse import urlunparse

def get_from_server(server_url, msg=""):
    try:
        response = requests.get(server_url, data=msg, timeout=2)
        if response.status_code != requests.codes.ok:
            exit(f"ERROR: server response code is {response.status_code}, with message: {response.reason}")
        return json.loads(response.text)['message']
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout)  as e:
        exit(f"ERROR: couldnt connect to Server at {server_url}, details:\n{e}")


def client_user_from_sample_user(sample_user):
    client_user = cortex_client_pb2.User()
    client_user.ParseFromString(sample_user.SerializeToString())
    return client_user


def client_snapshot_from_sample_snapshot(sample_snapshot):
    client_snapshot = cortex_client_pb2.Snapshot()
    client_snapshot.ParseFromString(sample_snapshot.SerializeToString())
    return client_snapshot


@click.group()
def main():
    pass


@main.command('get-users')
@click.option('-h', '--host', default="127.0.0.1", help='target api host')
@click.option('-p', '--port', default="5000", help='target api port')
def get_users(host, port):
    req_url = f"http://{host}:{port}/users"
    resp = get_from_server(req_url)
    if resp:
        print(tabulate(resp, headers="keys"))


if __name__ == "__main__":
    main()
