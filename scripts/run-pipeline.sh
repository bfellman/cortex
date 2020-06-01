#!/bin/bash
./scripts/install.sh
source .env/bin/activate
docker run -d -p 5672:5672 rabbitmq 
docker run -d -p 27017:27017 mongo
python -m cortex.server run-server --host 127.0.0.1 --port 8000 'rabbitmq://127.0.0.1:5672/' >& /tmp/server.log &
python -m cortex.parsers run-parser pose 'rabbitmq://127.0.0.1:5672/' >& /dev/null &
python -m cortex.parsers run-parser feelings 'rabbitmq://127.0.0.1:5672/' >& /dev/null &
python -m cortex.parsers run-parser color_image 'rabbitmq://127.0.0.1:5672/' >& /dev/null &
python -m cortex.parsers run-parser depth_image 'rabbitmq://127.0.0.1:5672/' >& /dev/null &
python -m cortex.saver run-saver mongodb://127.0.0.1:27017 rabbitmq://127.0.0.1:5672 >& /tmp/saver.log &
python -m cortex.api run-server --host 127.0.0.1 --port 5000 >& /tmp/api.log &
