import logging
import struct

import click
import requests

from cortex import cortex_client_pb2
from cortex import cortex_sample_pb2
from cortex.utils import agnostic_open

def upload_sample(host, port, path):
    """upload sample to server"""
    reader = sample_reader(path)
    server_url = f"http://{host}:{port}/"
    user_msg_url = server_url + "user"
    user = next(reader)
    send_msg_to_server(user.SerializeToString(), user_msg_url)
    snapshot_url = server_url + 'snapshot/' + str(user.user_id)
    for snapshot in reader:
        send_msg_to_server(snapshot.SerializeToString(), snapshot_url)


def send_msg_to_server(msg, server_url):
    logging.debug(f'Sending {msg} to {server_url}')
    try:
        response = requests.post(server_url, data=msg, timeout=2)
        if response.status_code != requests.codes.ok:
            exit(f"ERROR: server response code is {response.status_code}, with message: {response.reason}")
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
        exit(f"ERROR: couldn't connect to Server at {server_url}, details:\n{e}")


def client_user_from_sample_user(sample_user):
    client_user = cortex_client_pb2.User()
    client_user.ParseFromString(sample_user.SerializeToString())
    return client_user


def client_snapshot_from_sample_snapshot(sample_snapshot):
    client_snapshot = cortex_client_pb2.Snapshot()
    client_snapshot.ParseFromString(sample_snapshot.SerializeToString())
    return client_snapshot


def sample_reader(path):
    try:
        with agnostic_open(path, 'rb') as sample_fh:
            (msg_len,) = struct.unpack('I', sample_fh.read(4))
            sample_user = cortex_sample_pb2.User()
            sample_user.ParseFromString(sample_fh.read(msg_len))
            client_user = client_user_from_sample_user(sample_user)
            yield client_user
            while chunk := sample_fh.read(4):
                (msg_len,) = struct.unpack('I', chunk)
                sample_snapshot = cortex_sample_pb2.Snapshot()
                sample_snapshot.ParseFromString(sample_fh.read(msg_len), )
                client_snapshot = client_snapshot_from_sample_snapshot(sample_snapshot)
                yield client_snapshot
    except IOError:
        exit(f"ERROR: couldn't open file {path}")


@click.group()
def main():
    logging.basicConfig(filename='/tmp/.client.log', level=logging.INFO)
    pass


@main.command('upload-sample')
@click.option('-h', '--host', default="127.0.0.1", help='target host')
@click.option('-p', '--port', default="8000", help='target port')
@click.argument('path')
def upload_sample_cli(host, port, path):
    upload_sample(host, port, path)


if __name__ == "__main__":
    main()
