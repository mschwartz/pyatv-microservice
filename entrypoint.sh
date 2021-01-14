#!/bin/bash

ls -l
echo $MONGO_HOSTNAME
echo $MQTT_HOST

echo "==="
cat pyatv-microservice.py
echo "==="

nodemon ./pyatv-microservice.py 

echo "exited"
