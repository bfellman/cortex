import json

from urllib.parse import urlparse
import struct
from datetime import datetime
import pika
import click
import flask
import requests
from google import protobuf
from google.protobuf.json_format import MessageToDict
from cortex import cortex_client_pb2
from pathlib import Path
USERS_DIR = Path("./users")

app = flask.Flask(__name__)


@app.route('/', methods=['POST'])
def default_response():
    return flask.jsonify(success=False, message="Only supported requests are PORT with '/new_user' and '/snapshot' URLs")


@app.route('/user', methods=['POST'])
def publish_user():
    user_msg = flask.request.data
    user = cortex_client_pb2.User()
    try:
        user.ParseFromString(user_msg)
        Path.mkdir(USERS_DIR / str(user.user_id), exist_ok=True, parents=True)
        msg = MessageToDict(user, preserving_proto_field_name=True)
        msg['msg_type'] = 'user'
        app.config['PUBLISH'](json.dumps(msg))

    except protobuf.message.DecodeError as e:
        r = requests.Response()
        r.status_code = requests.codes.server_error
        r.reason = f"Expecting User in 'cortex_client_pb2' protobuf format, got:\n{e}"
        return r

    return flask.jsonify(success=True)


@app.route('/snapshot/<user_id>', methods=['POST'])
def publish_snapshot(user_id):
    snapshot_client_msg = flask.request.data
    snapshot_client = cortex_client_pb2.Snapshot()
    snapshot_client.ParseFromString(snapshot_client_msg)
    #build mq snapshot
    datetime_str = datetime.fromtimestamp(snapshot_client.datetime/ 1000).strftime('%Y-%m-%d_%H-%M-%S_%f')
    snapshot_dir = USERS_DIR / user_id / datetime_str
    snapshot_dir.mkdir(exist_ok=True)

    msg = MessageToDict(snapshot_client, preserving_proto_field_name=True)
    msg['user_id'] = user_id
    msg['msg_type'] = 'snapshot'
    color_image_path = snapshot_dir/"color_image"
    with open(color_image_path, 'wb') as fh:
        fh.write(snapshot_client.color_image.data)
    del msg['color_image']['data']
    msg['color_image']['path'] = str(color_image_path)
    # msg['color_image'] = {"width" : snapshot_client.color_image.width,
    #                       "height": snapshot_client.color_image.height,
    #                       "path" : color_image_path}
    depth_image_path = snapshot_dir / "depth_image"
    with open(depth_image_path, 'wb') as fh:
        for d in msg['depth_image']['data']:
            fh.write(struct.pack('f', d))
    del msg['depth_image']['data']
    msg['depth_image']['path'] = str(depth_image_path)
    app.config['PUBLISH'](json.dumps(msg))
    return flask.jsonify(success=True)



def print_message(message):
    print(message)

@click.group()
def main():
    pass


def get_rabbit_mq_publish_function(url):
    params = pika.ConnectionParameters(host=url.hostname, port=url.port)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange='cortex', exchange_type='topic')
    def publish(msg):
        return channel.basic_publish(exchange='cortex',
                                     routing_key='snapshot',
                                     body=msg)
    return publish

@main.command('run-server')
@click.option('-h', '--host', default="127.0.0.1", help='target host')
@click.option('-p', '--port', default="8000", help='target port')
@click.argument('publish')
def run_server_cli(host, port, publish):
    publish_url = urlparse(publish)
    publish_function = {'rabbitmq': get_rabbit_mq_publish_function(publish_url)}
    try:
        run_server(host, port, publish_function[publish_url.scheme])
    except KeyError as e:
        exit(f"Unknown publishing scheme '{e}', supported schemes are:\n{publish_function.keys()}")


def run_server(host, port, publish):
    app.config['PUBLISH'] = publish
    #TODO remove debug
    app.run(host, port, debug=True, threaded=True)


if __name__ == "__main__":
    main()

