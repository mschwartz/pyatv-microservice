# MQTT class

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("autelis/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("topic " + msg.topic + " message " + msg.payload.decode("utf-8"))


class MQTTSingleton:
    def start(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        print("MQTT connecting...", self.client)
    try:
        ret = self.client.connect("nuc1")
        print("connected " + str(ret))
        self.client.subscribe("hubitat/#")
        self.client.loop_start()
    except Exception as err:
        print("Connect Exception " + str(err))

    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("autelis/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print("topic " + msg.topic + " message " + msg.payload.decode("utf-8"))


print("new singleton")
MQTT = MQTTSingleton()
MQTT.start()
