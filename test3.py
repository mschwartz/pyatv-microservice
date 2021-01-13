import sys
import os
import json
import asyncio
import base64
import pyatv
from pyatv import convert, interface
from pyatv.const import FeatureName, FeatureState, PowerState
import paho.mqtt.client as mqtt
from pymongo import MongoClient

MQTT_HOST=os.environ.get("MQTT_HOST")
MONGO_HOST=os.environ.get("MONGO_HOST")

print("MQTT_HOST", MQTT_HOST)
print("MONGO_HOST", MONGO_HOST)

MQTT = mqtt.Client()

atvs = []
config = []

def find_config(name):
    for device in config:
        if device["name"] == name:
            return device
    return None

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("settings/status/config")


# set to True after settings received  once
# the second time message is received, we want to exit
settings = False

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global settings
    message = msg.payload.decode("utf-8")
    parts = msg.topic.split("/")
    dest = parts.pop()

    print(
        "\n\n\n=======> topic " + msg.topic + " message {}".format(msg),
        parts,
        dest,
        parts[0],
        "\n\n\n",
    )
    if dest == "config":
        if parts[0] == "settings":
            if settings:
                print("EXITING!")
                os._exit(0)

            settings = True


async def main():
    global config
    global atvs

    mongo = MongoClient(MONGO_HOST)
    db = mongo["settings"]
    collection = db.config
    raw = collection.find_one({"_id": "config"})
    for entry in raw["appletv"]["devices"]:
        # print("entry", entry["device"], entry)
        config.append(entry)

    loop = asyncio.get_event_loop()

    devices = await pyatv.scan(loop, timeout=5)
    if not devices:
        print("No apple tvs found", file=sys.stderr)
        return

    for device in devices:
        print(device)
        print("\n")

        found = find_config(device.name)
        if found:
            topic = "appletv/{}/set/command".format(device.name)
            MQTT.subscribe(topic)
            found['state'] = {
                "power": None,
                "app": None,
                "mediaType": None,
                "deviceState": None,
                "title": None,
                "artist": None,
                "album": None,
                "genre": None,
                "position": None,
                "total_time": None,
                "repeat": None,
                "shuffle": None,
                "artwork": None,
            };
            # connected = False
            # while not connected:
            #     try:
            #         print("CONNECTING TO ", device.address, device.name)
            #         atv = await pyatv.connect(device, loop)
            #         print(" -> CONNECTED", device.address)
            #         connected = True
            #     except Exception:
            #         await atv.close(loop)
            #         pass

            atv = device
            atvs.append({ 
                "config": found,
                "device": device,
                "atv": atv, 
                })

    while True:
        for item in atvs:
            device = item['device']
            name = device.name
            atv = item['atv']
            config = item['config']

            app = "None"
            try:
                app = atv.metadata.app.name
                # print(app)
            except Exception:
                app = "None"
           
            power = atv.power.power_state == PowerState.On
            playing = await atv.metadata.playing()
            o = {
                "power": power,
                "app": app,
                "mediaType": convert.media_type_str(playing.media_type),
                "deviceState": convert.device_state_str(playing.device_state),
                "title": playing.title,
                "artist": playing.artist,
                "album": playing.album,
                "genre": playing.genre,
                "position": playing.position,
                "total_time": playing.total_time,
                "repeat": convert.repeat_str(playing.repeat),
                "shuffle": convert.shuffle_str(playing.shuffle),
            }

            if o != config['state']:
                 MQTT.publish("info", json.dumps(o), retain=True)

            artwork = await atv.metadata.artwork(300, 300)
            if artwork:
                try:
                    tmp_filename = "/tmp/{}".format(name)
                    file = open(tmp_filename, "wb")
                    file.write(artwork.bytes)
                    file.close()

                    file = open(tmp_filename, "rb")
                    image_data_binary = file.read()
                    file.close()
                    try:
                        os.remove(tmp_filename)
                    finally:
                        pass

                    artwork = base64.b64encode(image_data_binary).decode("ascii")

                except Exception as err:
                    artwork = None

            o['artwork'] = artwork
            for attr, value in o.items():
#                 print("attr", attr, "value", value, config['state'][attr])
                if value != config["state"][attr]:
                    topic = "appletv/{}/status/{}".format(config['device'], attr)
                    if  device.name == "Office":
                        print(device.name, "publish", topic, value)
                    config['state'][attr] = o[attr]
                    MQTT.publish(topic, value, retain=True)

        await asyncio.sleep(1)


if __name__ == "__main__":
    print("MQTT connecting...")
    MQTT.on_connect = on_connect
    MQTT.on_message = on_message
    try:
        ret = MQTT.connect(MQTT_HOST)
        print("MQTT connected " + str(ret))
        # client.subscribe("hubitat/#")
        MQTT.loop_start()
    except Exception as err:
        print("MQTT Connect Exception " + str(err), err, MQTT_HOST)

    asyncio.get_event_loop().run_until_complete(main())


