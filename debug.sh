#!/usr/bin/env bash

# run container without making it a daemon - useful to see logging output
docker run \
    --rm \
    --name="pyatv-microservice" \
    --net=host\
    -e "MONGO_HOST=$MONGO_HOST" \
    -e "MQTT_HOST=$MQTT_HOSTNAME" \
    -v $PWD:/home/app \
    robodomo/pyatv-microservice
