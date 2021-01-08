import sys
import asyncio
import time
import base64
import json
import pyatv
from pyatv.const import FeatureName, FeatureState, PowerState
from pyatv import convert,interface
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

hosts = []  # list of AppleTVHost instances
devices = []  # list of devices from Config
host_map = {}  # map <hostname> => AppleTVHost instance


def find_device(name):
    for device in devices:
        if device["name"] == name:
            return device
    return None


client = mqtt.Client()

class PushListener(interface.PushListener):
    def __init__(self, host):
        self.host = host
        print("  construct PushListener", host.name);

    @staticmethod
    def playstatus_update(self, updater, playstatus):
        print("update", playstatus, flush= True)

    @staticmethod
    def playstatus_error(self, updater, exception):
        print("error", exception)

class DeviceListener(interface.DeviceListener):
    """Internal listener for generic device updates."""

    def __init__(self, host):
        self.host = host
        print("  construct DeviceListener", host.name);

    def connection_lost(self, exception):
        """Call when unexpectedly being disconnected from device."""
        print("Connection lost with error:", str(exception), file=sys.stderr)

    def connection_closed(self):
        """Call when connection was (intentionally) closed."""
        print("Connection was closed properly")

class AppleTVHost:
    def __init__(self, atv, config, loop):
        print(atv.device_info)
        self.atv = atv
        self.config = config
        self.name = config["device"]
        self.loop = loop
        self.state = {
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
        }
        topic = "appletv/{}/set/command".format(self.name)
        client.subscribe(topic)

    #


    async def publish(self, key, value):
        topic = "appletv/{}/status/{}".format(self.name, key)
#         print("publish", topic, value)
        client.publish(topic, value, retain=True)

    async def connect(self, loop):
        print("Connecting to {0} {1}".format(self.atv.address, self.atv.name))
        atv  = await pyatv.connect(self.atv, loop)

#         push_listener = PushListener(self)
#         device_listener = DeviceListener(self)
#         atv.listener = device_listener
#         atv.push_updater.listener = push_listener
#         atv.push_updater.start()
        self.device = atv;

#         print("started listener", self.device.push_updater.active, "\n\n")

    async def set_state(self, o):
        for attr, value in o.items():
            if o[attr] != self.state[attr]:
                await self.publish(attr, value)
                # print("new attr", attr)
                self.state[attr] = o[attr]
        # self.state = o

    async def run(self):
        power = self.device.power.power_state == PowerState.On
        playing = await self.device.metadata.playing()
        if self.name == "appletv-office":
            print(self.name, "playing\n", playing)
        app = "None"
        try:
            app = self.device.metadata.app.name
            # print(app)
        except Exception:
            app = "None"
            pass
            # print(self.name, "no app")

        print("\n");
        print("\n");
        print(self.name, "Power", power, "App", app)
        #### ARTWORK
        artwork = await self.device.metadata.artwork(300, 300)
        if artwork:
            try:
                tmp_filename = "/tmp/{}".format(self.name)
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

        if o != self.state:
            await self.publish("info", json.dumps(o))

        o["artwork"] = artwork
        await self.set_state(o)

        # self.state = o
        # print("\n\n\n")

    async def command(self, topic, message):
        print(self.name, "command", topic, message)

    #
    async def poweron(self):
        try:
            await self.device.power.turn_on()
            print(self.name, "powered on")
        except BaseException as e:
            print("**** ", self.name, "turn_on failed")

    #
    async def poweroff(self):
        try:
            # await self.device.remote_control.suspend()
            await self.device.remote_control.turn_off()
            print(self.name, "powered off")
        except BaseException as e:
            print("**** ", self.name, "turn_off failed")

    #
    async def home(self):
        try:
            await self.device.remote_control.home()
        except BaseException:
            print("home failed")

    #
    async def play(self):
        if self.name == "Office":
            try:
                await self.device.remote_control.play()
            except BaseException:
                print("play failed")

    #
    async def pause(self):
        if self.name == "Office":
            try:
                await self.device.remote_control.pause()
            except BaseException:
                print("pause failed")

    #
    def __del__(self):
        print(self.name, "destruct")


# Method that is dispatched by the asyncio event loop
async def init_appletvs(loop):
    """Find a device and print what is playing."""
    print("Discovering devices on network...")
    atvs = await pyatv.scan(loop, timeout=5)

    if not atvs:
        print("No device found", file=sys.stderr)
        return

    for atv in atvs:
        # print("==========\n", "atv", atv, "\n")
        device = find_device(atv.name)
        if device != None and atv.name == "Office":
            hostname = device["device"]
            print("new host", hostname)
            host = AppleTVHost(atv, device, loop)
            hosts.append(host)
            host_map[hostname] = host
            await host.connect(loop)
#             print("RUN")
            await host.run()
            # if host.name == "Office":
            #     await host.play()
            # else:
#             await host.poweroff()

#     print("\n\n")
#     print("Connecting to {0} {1}".format(atvs[0].address, atvs[0].name))
    # atv = await pyatv.connect(atvs[0], loop)

#     while True:
#          time.sleep(1)
    while True:
        for atv in hosts:
            await atv.run()
#         print("sleep")
        time.sleep(1)


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
    hosts = []
    mongo = MongoClient(os.environ.get("MONGO_HOST"))
    db = mongo["settings"]
    collection = db.config
    raw = collection.find_one({"_id": "config"})
    for atv in raw["appletv"]["devices"]:
        print("atv", atv["device"], atv)
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
    LOOP.run_until_complete(init_appletvs(LOOP))


if __name__ == "__main__":
    # Setup event loop and connect
    print("starting")
    main()
    print("stopping")
    # LOOP.run_until_complete(init_appletvs(LOOP))
