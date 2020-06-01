import json
from pathlib import Path
from urllib.parse import urlparse

import click
import gridfs
import mongomock
import pika
from pymongo import MongoClient, ASCENDING
from mongomock.gridfs import enable_gridfs_integration


class Saver:
    def __init__(self, database_url):
        parsed_url = urlparse(database_url)
        if 'mongo' in parsed_url.scheme:
            if 'mongodb' == parsed_url.scheme:
                client = MongoClient(parsed_url.hostname, parsed_url.port)
                client.drop_database('cortex_db')
            elif 'mockmongo' == parsed_url.scheme:
                client = mongomock.MongoClient(parsed_url.hostname, parsed_url.port, connect=True)
                enable_gridfs_integration()
            else:
                exit(f"Unknown DB {parsed_url.scheme}")
            self.db = client.cortex_db
            self.fs = gridfs.GridFS(self.db)
            self.db.users.create_index([("user_id", ASCENDING)], unique=True)
            self.db.snapshots.create_index([("user_id", ASCENDING), ("datetime", ASCENDING)])
        else:
            exit(f"Unknown DB {parsed_url.scheme}")

    def save(self, topic_name, data):
        unpacked_data = json.loads(data)
        if topic_name in unpacked_data:
            topic_dict = unpacked_data[topic_name]
            snapshot_key = {"user_id": unpacked_data['user_id'], 'datetime': unpacked_data['datetime']}
            for k, v in topic_dict.items():
                path_v = Path(str(v))
                if path_v.exists():
                    topic_dict[k] = self.fs.put(open(v, 'rb'), suffix=path_v.suffix)
            if self.db.snapshots.find_one(snapshot_key):
                self.db.snapshots.update_many(snapshot_key, {'$set': {topic_name: topic_dict}})
            else:
                try:
                    snapshot_id = self.db.snapshots.find_one({'$query': {"user_id": unpacked_data['user_id']}, '$orderby': {'_id': -1}})['_id']+1
                except:
                    assert self.db.snapshots.count_documents({}) == 0, "if we didn't find any snapshot, the db must be empty"
                    snapshot_id = 0
                snapshot_key['_id'] = snapshot_id
                self.db.snapshots.insert_one(snapshot_key, {'$set': {topic_name: topic_dict}})

    def add_user(self, user_dict):
        self.db.users.update_one({'user_id': user_dict['user_id']}, {'$set': user_dict}, upsert=True)

    def handle_snapshot(self, data):
        # listen to all snapshots to catch user id
        unpacked_data = json.loads(data)
        if unpacked_data['msg_type'] == 'user':
            self.add_user(unpacked_data)


@click.group()
def main():
    pass


@main.command('save')
@click.argument('topic')
@click.argument('path_to_data')
@click.option('-d', '--database', default="mongodb://127.0.0.1:27017", help="url to database engine")
def saver_cli(topic, path_to_data, database):
    """"saves <data> to <topic> in database"""
    try:
        with open(path_to_data, 'r') as fh:
            data = fh.read()
    except IOError as e:
        exit(f"ERROR reading file {path_to_data}\n{e}")
    Saver(database).save(topic, data)


@main.command('run-saver')
@click.argument('db_url_str')
@click.argument('mq_url_str')
def run_saver_cli(db_url_str, mq_url_str):
    """Usage:  python -m cortex.saver run-saver <database_url>> <message_queue_url> """
    saver = Saver(db_url_str)
    mq_url = urlparse(mq_url_str)
    if mq_url.scheme == 'rabbitmq':
        params = pika.ConnectionParameters(host=mq_url.hostname, port=mq_url.port)
        try:
            connection = pika.BlockingConnection(params)
        except Exception as e:
            exit(f"ERROR: can't connect to message queue: {mq_url.geturl()}\n{e}")
        channel = connection.channel()
        # receiving queue
        recv_queue_name = 'saver'
        channel.queue_declare(recv_queue_name)
        channel.queue_bind(exchange='cortex', queue=recv_queue_name, routing_key='*')

        def parse_msg(channel, method, properties, body):
            if method.routing_key == 'snapshot':
                saver.handle_snapshot(body)
            else:
                saver.save(method.routing_key, body)
        channel.basic_consume(
            queue=recv_queue_name, on_message_callback=parse_msg, auto_ack=True)
        channel.start_consuming()
    else:
        exit(f"Unsupported message queue format {mq_url.scheme}")


if __name__ == "__main__":
    main()
