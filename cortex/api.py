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
    return flask.jsonify(success=False, message=f"Only supported requests are {app.url_map}")

@app.route('/users', methods=['GET'])
def get_users():
    users = [project(d, ['user_id', 'username']) for d in app.config['DB'].users.find()]
    return flask.jsonify(success=True, message=users)


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

