#!/usr/bin/env bash

echo docker run \
    -d \
    --rm \
    -e "MONGO_HOST=$MONGO_HOSTNAME" \
    -e "MQTT_HOST=$MQTT_HOST" \
    --name="pyatv-microservice" \
    robodomo/pyatv-microservice
docker run \
    -d \
    --rm \
    -e "MONGO_HOST=$MONGO_HOSTNAME" \
    -e "MQTT_HOST=$MQTT_HOST" \
    --name="pyatv-microservice" \
    robodomo/pyatv-microservice
