import json
from pprint import pprint

from urllib.parse import urlparse
import struct
from datetime import datetime
import pika
import click
import flask
import requests
from google import protobuf
from google.protobuf.json_format import MessageToDict
from pymongo import MongoClient

from cortex import cortex_client_pb2
from pathlib import Path
from funcy import project
app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def default_response():
    return flask.jsonify(success=False, message=f"Only supported requests are {app.url_map}"), requests.codes.bad_request


@app.route('/users', methods=['GET'])
def get_users():
    users = [project(d, ['user_id', 'username']) for d in app.config['DB'].users.find()]
    return flask.jsonify(success=True, message=users)


@app.route('/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    res = app.config['DB'].users.find_one({'user_id': user_id})
    if res is None:
        return flask.jsonify(success=False, message=f"couldn't find {user_id=}"), requests.codes.not_found
    user_data = project(res, ['user_id', 'username', 'birthday', 'gender'])
    return flask.jsonify(success=True, message=user_data)


@app.route('/users/<user_id>/snapshots', methods=['GET'])
def get_user_snapshots(user_id):
    res = app.config['DB'].snapshots.find({'user_id': user_id})
    if res is None:
        return flask.jsonify(success=False, message=f"couldn't find {user_id=}"), requests.codes.not_found
    snapshots = [project(d, ['user_id', 'datetime', '_id']) for d in res]
    return flask.jsonify(success=True, message=snapshots)


@app.route('/users/<user_id>/snapshots/<snapshot_id>', methods=['GET'])
def get_snapshot_topics(user_id, snapshot_id):
    res = app.config['DB'].snapshots.find_one({'user_id': user_id, '_id': int(snapshot_id)})
    print(res)
    if res is None:
        return flask.jsonify(success=False, message=f"couldn't find {snapshot_id=} for {user_id=}"), requests.codes.not_found
    return flask.jsonify(success=True, message=res)


@click.group()
def main():
    pass

@main.command('run-server')
@click.option('-h', '--host', default="127.0.0.1", help='target host')
@click.option('-p', '--port', default="5000", help='target port')
@click.option('-d', '--database', default="mongodb://127.0.0.1:27017", help='database url')
def run_api_server_cli(host, port, database):
    run_api_server(host, port, database)


def connect_to_db(db_url):
    parsed_url = urlparse(db_url)
    if parsed_url.scheme == 'mongodb':
        client = MongoClient(parsed_url.hostname, parsed_url.port)
        return client.cortex_db
    else:
        exit("Unknown DB")


def run_api_server(host, port, database_url):
    app.config['DB'] = connect_to_db(database_url)
    app.run(host, port, debug=True, threaded=True)


if __name__ == "__main__":
    main()

