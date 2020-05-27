import json
from pprint import pprint

from urllib.parse import urlparse
import click
import flask
import gridfs
import hyperlink
import requests
from bson import objectid
from pymongo import MongoClient
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
    db_res = app.config['DB'].users.find_one({'user_id': user_id})
    if db_res is None:
        return flask.jsonify(success=False, message=f"couldn't find {user_id=}"), requests.codes.not_found
    user_data = project(db_res, ['user_id', 'username', 'birthday', 'gender'])
    return flask.jsonify(success=True, message=user_data)


@app.route('/users/<user_id>/snapshots', methods=['GET'])
def get_user_snapshots(user_id):
    db_res = app.config['DB'].snapshots.find({'user_id': user_id})
    if db_res is None:
        return flask.jsonify(success=False, message=f"couldn't find {user_id=}"), requests.codes.not_found
    snapshots = [project(d, ['user_id', 'datetime', '_id']) for d in db_res]
    return flask.jsonify(success=True, message=snapshots)


@app.route('/users/<user_id>/snapshots/<snapshot_id>', methods=['GET'])
def get_snapshot_results(user_id, snapshot_id):
    db_res = app.config['DB'].snapshots.find_one({'user_id': user_id, '_id': int(snapshot_id)})
    results = [k for k, v in db_res.items() if isinstance(v, dict)]
    if db_res is None:
        return flask.jsonify(success=False, message=f"couldn't find {snapshot_id=} for {user_id=}"), requests.codes.not_found
    return flask.jsonify(success=True, message=results)

@app.route('/users/<user_id>/snapshots/<snapshot_id>/<result_name>', methods=['GET'])
def get_result_data(user_id, snapshot_id, result_name):
    db_res = app.config['DB'].snapshots.find_one({'user_id': user_id, '_id': int(snapshot_id)})
    if db_res is None:
        return flask.jsonify(success=False, message=f"couldn't find {snapshot_id=} for {user_id=}"), requests.codes.not_found
    if result_name not in db_res:
        return flask.jsonify(success=False, message=f"couldn't find {result_name} in {snapshot_id=} for {user_id=}"), requests.codes.not_found
    for k, v in db_res[result_name].items():
        if isinstance(v, objectid.ObjectId):
            suffix = app.config['FS'].get(v).suffix.lstrip('.')
            print(suffix)
            if suffix in ['jpeg']:
                db_res[result_name][k] = f"http:://{app.config['HOST_URL']}/get_file/image/{suffix}/{v}"
    print(app.__dict__)
    return flask.jsonify(success=True, message=db_res[result_name])

@app.route('/get_file/<f_type>/<f_format>/<file_id>', methods=['GET'])
def get_jpg_file(f_type, f_format, file_id):
    fs_res = app.config['FS'].get(objectid.ObjectId(file_id))
    return app.response_class(fs_res.read(), direct_passthrough=True, mimetype=f_type + '/' + f_format)



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
        return client.cortex_db, gridfs.GridFS(client.cortex_db)
    else:
        exit("Unknown DB")


def run_api_server(host, port, database_url):
    app.config['DB'], app.config['FS'] = connect_to_db(database_url)
    app.config['HOST_URL'] = f"{host}:{port}"
    app.run(host, port, debug=True, threaded=True)


if __name__ == "__main__":
    main()

