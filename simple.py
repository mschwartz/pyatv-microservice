import sys
import asyncio
import time
import base64
import json
import pyatv
from pyatv.const import FeatureName, FeatureState, PowerState
from pyatv import convert, interface
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import os

# import PIL
from PIL import Image
from io import BytesIO
import io

# import MQTT

# import base64
# import cStringIO


LOOP = asyncio.get_event_loop()

devices = []  # list of devices from Config
host_map = {}  # map <hostname> => AppleTVHost instance
config_map = {}


def find_device(name):
    for device in devices:
        if device["name"] == name:
            return device
    return None


client = mqtt.Client()


class PushListener(interface.PushListener):
    def __init__(self, device):
        self.device = device
        print("  construct PushListener", device)

    @staticmethod
    def playstatus_update(self, updater, playstatus):
        print("update", playstatus, flush=True)

    @staticmethod
    def playstatus_error(self, updater, exception):
        print("error", exception)


class DeviceListener(interface.DeviceListener):
    """Internal listener for generic device updates."""

    def __init__(self, host):
        self.host = host
        print("  construct DeviceListener", host.name)

    def connection_lost(self, exception):
        """Call when unexpectedly being disconnected from device."""
        print("Connection lost with error:", str(exception), file=sys.stderr)

    def connection_closed(self):
        """Call when connection was (intentionally) closed."""
        print("Connection was closed properly")


# Method that is dispatched by the asyncio event loop
async def init_appletvs():
    """Find a device and print what is playing."""

    loop = asyncio.get_event_loop()
    print("Discovering devices on network...")
    atvs = await pyatv.scan(loop, timeout=5)

    if not atvs:
        print("No device found", file=sys.stderr)
        return

    for atv in atvs:
        device = find_device(atv.name)
        print("==========\n", "atv", atv.name, device, "\n")
        if device != None and atv.name == "THEATER":
            print("Connecting")
            hostname = device["device"]
            box = await pyatv.connect(atv, loop)
            print("connected!", atv.address, atv.name)
            # listener = PushListener(device)
            # box.push_updater.listener = listener;
            # box.push_updater.start()

    loop.run_in_executor(None, sys.stdin.readline)


# The callback for when the client receives a CONNACK response from the server.
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


def main():
    mongo = MongoClient(os.environ.get("MONGO_HOST"))
    db = mongo["settings"]
    collection = db.config
    raw = collection.find_one({"_id": "config"})
    for atv in raw["appletv"]["devices"]:
        # print("atv", atv["device"], atv)
        devices.append(atv)
    # print("raw", raw['appletv']['devices'])
    # config = json.loads(str(raw))
    # print("config", config)

    print("connecting...")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        ret = client.connect("nuc1")
        print("connected " + str(ret))
        # client.subscribe("hubitat/#")
        client.loop_start()
    except Exception as err:
        print("Connect Exception " + str(err))

    #     asyncio.async(init_appletvs())
    #     asyncio.async(init_appletvs())
    #     LOOP.run_forever()
    asyncio.get_event_loop().run_until_complete(init_appletvs())


if __name__ == "__main__":
    # Setup event loop and connect
    print("starting")
    main()
    print("stopping")
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    # LOOP.run_until_complete(init_appletvs(LOOP))
