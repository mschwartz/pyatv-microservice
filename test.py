import sys
import asyncio
import pyatv
import paho.mqtt.client as mqtt

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
    print(dir(pyatv))
    print('Connecting to {0}'.format(atvs[0].address))
    atv = await pyatv.connect_to_apple_tv(atvs[0], loop)

    try:
        playing = await atv.metadata.playing()
        print('Currently playing:')
        print(playing)
    finally:
        # Do not forget to close
        await atv.close()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hubitat/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("message " + msg.topic+" "+str(msg.payload))


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("connecting...")
    client.connect("nuc1")
    print("still connecting...")
    client.subscribe("hubitat/#")


    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


if __name__ == '__main__':
    # Setup event loop and connect
    main()
    # LOOP.run_until_complete(print_what_is_playing(LOOP))
