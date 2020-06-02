[![Build Status](https://travis-ci.org/bfellman/cortex.svg?branch=master)](https://travis-ci.org/bfellman/cortex)
[![codecov](https://codecov.io/gh/bfellman/cortex/branch/master/graph/badge.svg)](https://codecov.io/gh/bfellman/cortex)
# Cortex Thought Processing System

## Intro
The Cortex system enables user to store snapshots of their thoughts in remote server, for further processing and storage.
The system simulates a [client](#client) uploading data (as the hardware device doesn't exist yet), and implements a remote [server](#server) communicating with a variety of [parsers](#parsers) through a [message queue](#message-queue).
Parsed results are [stored to a database](#saver), exposed by a [web API](#web-api) and can be accessed by a [CLI](#cli)   
![system_arch_images](https://github.com/bfellman/cortex/blob/master/cortex_arch.png)

This is the final project in [Advanced System Design](https://advanced-system-design.com/) course, given in Tel-Aviv University on  winter 2019-2020

## Contents
  * [Intro](#intro)
  * [Setup](#setup)
    + [Requirements](#requirements)
  * [System Components](#system-components)
    + [Client](#client)
    + [Server](#server)
    + [Message Queue](#message-queue)
    + [Parsers](#parsers)
    + [Saver](#saver)
    + [Web API](#web-api)
    + [CLI](#cli)
  * [TODOs](#todos)

## Setup
First Clone the repo:
```bash
$ git clone https://github.com/bfellman/cortex.git
```
Then install and activate:
```bash
$ cd cortex
$ ./scripts/install.sh
… 
$ source .env/bin/activate
[cortex] $ 
```
Finally, enable all background services:
```bash
$ sudo ./scripts/run-pipline.sh # use sudo for launching docker images
``` 
### Requirements
- `docker` for running [message queue](#message-queue) and database
- `python3.8`, `virtualenv` and `pip` 

## System Components
### Client
The client expect to receive a `SNAPSHOT.mind.gz` file in protobuf format, where the first message is the User information, and the rest are snapshots.

Run client using CLI:
``` bash
$ python -m cortex.client upload-sample --host '127.0.0.1' --port 8000 '<SNAPSHOT.mind.gz>'
# '--host' and '--port' are optioanl knobs, the above value is their default
```
Example for such a file is provided in [tests/inputs/3_entries.mind.gz](tests/inputs/3_entries.mind.gz]), so you can try it out of the box:
```bash
$ python -m cortex.client upload-sample tests/inputs/3_entries.mind.gz
```

File protobuf format defined in [cortex/protos/cortex.proto](cortex/protos/cortex.proto), note that each protobuf snapshot message is preceded by a uint32 specifiying the expected message size   

### Server
Launched using [scripts/run-pipeline.sh](scripts/run-pipeline.sh), but can be run directly using CLI:
``` bash
$ python -m cortex.server run-server --host '127.0.0.1' --port 8000 'rabbitmq://127.0.0.1:5672/'
# '--host' and '--port' are optioanl knobs, the above value is their default
```
The positional argument is a URL to a [message queue](#message-queue). Currently, only `RabbitMQ` is supported (host and port default values are aligned with the ones used in [scripts/run-pipeline.sh](scripts/run-pipeline.sh)) 

Note that the server doesn't send raw data of big files, but rather stores data to a temporary location and sends the path on [message queue](#message-queue) (assuming future consumers share FS. and will access it soon)  
### Message Queue
All services are connected through `RabbitMQ`, and share a `topic` exchange.
The [server](#server) publishes under the `snapshot` topic, and the [parsers](#parsers) publish under their dedicated topics

### Parsers
Parsers are defined in [cortex/parser_dir](cortex/parser_dir), any function of this format `parse_<TOPIC>(data)` is considered a parser, and will be activated on any message in the [message queue](#message-queue) sent with TOPIC attribute.

`cortex.parsers` provides a listener for each parser, that can be triggered using `run-parser`. It is launched using [scripts/run-pipeline.sh](scripts/run-pipeline.sh), but can be run directly using CLI:
```bash
$ python -m cortex.parsers run-parser TOPIC 'rabbitmq://127.0.0.1:5672/'
```
Note that the parsers doesn't send raw data of big files, but rather stores data to a temporary location and sends the path on [message queue](#message-queue) (assuming future consumers share FS. and will access it soon)
New parsers can be added by simply placing them in the [cortex/parser_dir](cortex/parser_dir), using the above format.

Existing parsers:

|Name| Defined in | Description |
|----|------------|------------------------------------|
|pose| [cortex/parser_dir/pose.py](cortex/parser_dir/pose.py)| Collects the translation and the rotation of the user's head at a given timestamp, and publishes the result to a dedicated topic|
|color_image | [cortex/parser_dir/color_image.py](cortex/parser_dir/color_image.py) | color_image | Collects the color image of what the user was seeing at a given timestamp, and publishes the result to a dedicated topic|
|depth_image | [cortex/parser_dir/depth_image.py](cortex/parser_dir/depth_image.py)| Collects the depth image of what the user was seeing at a given timestamp, and publishes the result to a dedicated topic. A depth image is a width × height array of floats, where each float represents how far the nearest surface from the user was, in meters. So, if the user was looking at a chair, the depth of its outline would be its proximity to her (for example, 0.5 for half a meter), and the wall behind it would be farther (for example, 1.0 for one meter). Represented using matplotlib's heatmap.|
|feelings|[cortex/parser_dir/feelings.py](cortex/parser_dir/feelings.py) |Collects the feelings the user was experiencing at any timestamp, and publishes the result to a dedicated topic|
 
### Saver
The Saver listens to [message queue](#message-queue) and stores parsed results to MongoDB database, while raw data is stored in GridFS and MongoDB only holds a pointer to the GridFS object. 

Saver is launched using [scripts/run-pipeline.sh](scripts/run-pipeline.sh), but can be run directly using CLI:
```bash
$ python -m cortex.saver run-saver 'mongodb://127.0.0.1:27017'  'rabbitmq://127.0.0.1:5672/'
```
Where the first positional arg is Database URL, and the second one is Message Queue URL 
 
### Web API
The Web API provides a few RESTful endpoints for CLI and future GUI to access. It is launched using [scripts/run-pipeline.sh](scripts/run-pipeline.sh), but can be run directly using CLI:
```bash
$ python -m cortex.api run-server --host '127.0.0.1' --port 5000 
# '--host' and '--port' are optioanl knobs, the above value is their default
```
The following endpoints are supported:

|REST CMD| Result|
|---------------|--------------------|
|GET /users | Returns the list of all the supported users, including their IDs and names only|
|GET /users/user-id | Returns the specified user's details: ID, name, birthday and gender|
|GET /users/user-id/snapshots| Returns the list of the specified user's snapshot IDs and datetimes only|
|GET /users/user-id/snapshots/snapshot-id | Returns the specified snapshot's details: ID, datetime, and the available results' names only (e.g. pose)|
|GET /users/user-id/snapshots/snapshot-id/result-name | Returns the specified snapshot's result in a reasonable format. And provides links to heavy files|


### CLI
The CLI reflects the [API](#web-api), with the following commands:
```bash
$ python -m cortex.cli get-users
$ python -m cortex.cli get-user <USED_ID>
$ python -m cortex.cli get-snapshots <USED_ID>
$ python -m cortex.cli get-snapshot <USED_ID> <SNAPSHOT_ID>
$ python -m cortex.cli get-result <USED_ID> <SNAPSHOT_ID> <RESULT_NAME>
```
example output:
```bash
$ python -m cortex.cli get-users
  user_id  username
---------  ----------
       42  Dan Gittik

$ python -m cortex.cli get-user 42
birthday    gender      user_id  username
----------  --------  ---------  ----------
1992-03-05  MALE             42  Dan Gittik

$ python -m cortex.cli get-snapshots 42 | head
# snapshots for user_id='42'
  _id  datetime                      user_id
-----  --------------------------  ---------
    0  2019-12-04T10:08:07.339000         42
    1  2019-12-04T10:08:07.412000         42
    2  2019-12-04T10:08:07.476000         42
    3  2019-12-04T10:08:07.541000         42
    4  2019-12-04T10:08:07.603000         42
    5  2019-12-04T10:08:07.662000         42
    6  2019-12-04T10:08:07.734000         42

$ python -m cortex.cli get-snapshot 42 142
results
-----------
pose
color_image
depth_image

$ python -m cortex.cli get-result 42 142 color_image
# color_image for user_id='42' snapshot_id='142':
path                                                                   size
---------------------------------------------------------------------  ---------
http://://127.0.0.1:5000/get_file/image/jpeg/5ed573c8af11e636460808c9  1920x1080

```

## TODOs
Future features are listed under [project issues](https://github.com/bfellman/cortex/issues)