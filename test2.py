import sys
import asyncio
import time
import base64
import json
import pyatv
from pyatv.const import FeatureName, FeatureState, PowerState
from pyatv import convert
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import os

# import PIL
from PIL import Image
from io import BytesIO
import io
# import base64
# import cStringIO


LOOP = asyncio.get_event_loop()

hosts = []


class AppleTVHost:
    def __init__(self, atv, loop):
        print("Construct", atv.name)
        print(atv.device_info)
        self.atv = atv
        self.name = atv.name
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

    #

    async def connect(self):
        print("Connecting to {0} {1}".format(self.atv.address, self.atv.name))
        self.device = await pyatv.connect(self.atv, self.loop)

        
    async def run(self):
        power = self.device.power.power_state == PowerState.On
        print(self.name, power)
        playing = await self.device.metadata.playing()
        print(self.name, "Currently playing:")
        app = "None"
        try:
            app = self.device.metadata.app.name
            print(app)
        except Exception:
            print(self.name, "no app")

        #### ARTWORK
        artwork = await self.device.metadata.artwork(300, 300)
        if artwork:
            print(self.name, "artwork:")
            try:
                file = open("/tmp/foo.jpg", "wb")
                file.write(artwork.bytes)
                file.close()

                file = open("/tmp/foo.jpg", "rb")
                image_data_binary = file.read()
                file.close()
                try:
                    os.remove("/tmp/foo.jpg");
                finally:
                    pass
                
                artwork = base64.b64encode(image_data_binary).decode('ascii')

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
            "artwork": artwork,
        }

        for attr, value in o.items():
            if o[attr] != self.state[attr]:
                print("new attr", attr)
        self.state = o
        print("\n\n\n")

























        
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
        # if (
        #     self.device.features.get_feature(FeatureName.TurnOff)
        #     == FeatureState.Available
        # ):
        # await self.device.power.turn_off()
        # else:
        #     print("Can't turn_off ", self.name)

    #
    async def home(self):
        try:
            await self.device.remote_control.home()
        except BaseException:
            print("home failed")

    #
    async def stop(self):
        try:
            await self.device.remote_control.stop()
        except BaseException:
            print("stop failed")

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
        print("dstruct")


# Method that is dispatched by the asyncio event loop
async def print_what_is_playing(loop):
    """Find a device and print what is playing."""
    print("Discovering devices on network...")
    atvs = await pyatv.scan(loop, timeout=5)

    if not atvs:
        print("No device found", file=sys.stderr)
        return

    for atv in atvs:
        print("==========\n", "atv", atv, "\n")
        host = AppleTVHost(atv, loop)
        await host.connect()
        hosts.append(host)
        # if host.name == "Office":
        #     await host.play()
        # else:
        await host.poweroff()
        await host.run()

    # print("Connecting to {0} {1}".format(atvs[0].address, atvs[0].name))
    # atv = await pyatv.connect(atvs[0], loop)

    try:
        while True:
            for atv in hosts:
                await atv.run()
            # playing = await atv.metadata.playing()
            # print("Currently playing:")
            # print(playing)
            time.sleep(10)
    finally:
        # Do not forget to close
        atv.close()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("autelis/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("topic " + msg.topic + " message " + msg.payload.decode("utf-8"))


def main():
    mongo = MongoClient(os.environ.get("MONGO_HOST"))
    db = mongo["settings"]
    collection = db.config
    raw = collection.find_one({ '_id': "config" })
    print("raw", raw['appletv'])
    # config = json.loads(str(raw))
    # print("config", config)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    print("connecting...")
    try:
        ret = client.connect("nuc1")
        print("connected " + str(ret))
        # client.subscribe("hubitat/#")
        client.loop_start()
    except Exception as err:
        print("Connect Exception " + str(err))

    LOOP.run_until_complete(print_what_is_playing(LOOP))


if __name__ == "__main__":
    # Setup event loop and connect
    print("starting")
    main()
    # LOOP.run_until_complete(print_what_is_playing(LOOP))
