import importlib.util
import json
from pathlib import Path
from urllib.parse import urlparse

import click
import pika

PARSER_DIR = (Path(__file__).parent / "parser_dir")


def get_all_parsers():
    module_files = PARSER_DIR.glob("*.py")
    parsers = dict()
    for m_file in module_files:
        spec = importlib.util.spec_from_file_location(m_file.stem, m_file.absolute())
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for p in dir(module):
            if p.startswith('parse_') and callable(module.__getattribute__(p)):
                parsers[p.split('parse_')[1]] = module.__getattribute__(p)
    return parsers


def parse(parser_name, data):
    parsers = get_all_parsers()
    try:
        return parsers[parser_name](data)
    except KeyError:
        exit(f"ERROR: unknown parser '{parser_name}', available parsers are:'\n{list(parsers.keys())}")


@click.group()
def main():
    pass


@main.command('parse')
@click.argument('parser_name')
@click.argument('data')
def parse_cli(parser_name, path_to_data):
    """Usage:  python -m cortex.parsers parse <parser_name>> <path_to_data>"""
    try:
        data = open(path_to_data, "rb").read()
        print(parse(parser_name, data))
    except Exception as e:
        print(f"ERROR reading file {path_to_data}\n{e}")


@main.command('run-parser')
@click.argument('parser_name',)
@click.argument('mq_url')
def run_parser_cli(parser_name, mq_url):
    """Usage:  python -m cortex.parsers run-parser <parser_name>> <message_queue_url> """
    run_parser_server(mq_url, parser_name)


def run_parser_server(mq_url, parser_name):
    parsers = get_all_parsers()
    if parser_name not in parsers:
        exit(f"ERROR: unknown parser '{parser_name}', available parsers are:'\n{list(parsers.keys())}")
    publish_url = urlparse(mq_url)
    if publish_url.scheme == 'rabbitmq':
        params = pika.ConnectionParameters(host=publish_url.hostname, port=publish_url.port)
        try:
            connection = pika.BlockingConnection(params)
        except Exception as e:
            exit(f"ERROR: can't connect to message queue: {mq_url}\n{e}")
        channel = connection.channel()
        # receiving queue
        recv_queue_name = parser_name
        channel.queue_declare(recv_queue_name)
        channel.queue_bind(exchange='cortex', queue=recv_queue_name, routing_key='snapshot')

        def parse_msg(channel, method, properties, body):
            result = parse(parser_name, body)
            if result:
                channel.basic_publish(exchange='cortex',
                                      routing_key=parser_name,
                                      body=json.dumps(result))

        channel.basic_consume(
            queue=recv_queue_name, on_message_callback=parse_msg, auto_ack=True)
        channel.start_consuming()
    else:
        exit(f"Unsupported message queue format {publish_url.scheme}")


if __name__ == "__main__":
    main()
