import sys
import os
import asyncio
import pyatv
import paho.mqtt.client as mqtt


class AppleTV:
    """An instance of this handles one AppleTV on the network"""

    def __init__(self, name):
        self.name = name


LOOP = asyncio.get_event_loop()


# Method that is dispatched by the asyncio event loop
async def print_what_is_playing(loop):
    """Find a device and print what is playing."""
    print('Discovering devices on network...')
    atvs = await pyatv.scan_for_apple_tvs(loop, timeout=5)

    if not atvs:
        print('No device found', file=sys.stderr)
        return

    for atv in atvs:
        print("Name: {0}, Address: {1}".format(atv.name, atv.address))
    print('Connecting to {0}'.format(atvs[0].address))

    try:
        print("atv " + str(atvs[0]))
        atv = await pyatv.connect_to_apple_tv(atvs[0], loop)
        playing = await atv.metadata.playing()
        print('Currently playing:')
        print(playing)
    except Exception as err:
        print("Exception " + str(err))
    finally:
        # Do not forget to close
        await atv.close()


async def find_atvs(loop):
    print('Discovering devices on network...')
    atvs = await pyatv.scan_for_apple_tvs(loop, timeout=5)

    if not atvs:
        print('No device found', file=sys.stderr)
        return

    for atv in atvs:
        print("Name: {0}, Address: {1}".format(atv.name, atv.address))


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hubitat/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("message " + msg.topic + " " + str(msg.payload))


def main():
    # print("ATVs " + os.environ['ATVS'])
    LOOP.run_until_complete(find_atvs(LOOP))
    # await find_atvs(LOOP)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("connecting...")
    try:
        ret = client.connect("robodomo")
        print("connected " + str(ret))
        client.subscribe("hubitat/#")
        client.loop_forever()
    except Exception as err:
        print("Connect Exception " + str(err))

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.


if __name__ == '__main__':
    # Setup event loop and connect
    # main()
    # asyncio.run(main())
    LOOP.run_until_complete(print_what_is_playing(LOOP))
