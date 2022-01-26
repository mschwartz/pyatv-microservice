#
#
import sys
import os
import socket
import json
import asyncio
import base64
import pyatv
from pyatv import convert, interface
from pyatv.const import FeatureName, FeatureState, PowerState, Protocol
import paho.mqtt.client as mqtt
from pymongo import MongoClient

MQTT_HOST=os.environ.get("MQTT_HOSTNAME")
MONGO_HOST=os.environ.get("MONGO_HOST")

print("MQTT_HOST", MQTT_HOST)
print("MONGO_HOST", MONGO_HOST)

MQTT = mqtt.Client()

atvs = []
atv_map = {}
device_map = {}
config = []
config_map = {}

command_queue = []

def find_config(name):
#     print(config)
    for device in config:
#         print("find", name, device["name"])
        if device["name"] == name:
            return device
    return None

def find_device(host):
    for device in config:
        if device["device"] == host:
            return device
    return None

def on_connect(client, userdata, flags, rc):
    print("MQTT Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("settings/status/config")
    client.subscribe("appletv/reset/set/command");

# set to True after settings received  once
# the second time message is received, we want to exit
settings = False

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global settings
    message = msg.payload.decode("utf-8").upper()
    parts = msg.topic.split("/")
    dest = parts.pop()

#     print(
#             "\n\n\n=======> topic " + msg.topic + " message {}".format(message[:40]),
#         parts,
#         dest,
#         "\n\n\n",
#     )
    if dest == "config":
        if parts[0] == "settings":
            if settings:
                print("EXITING!")
                os._exit(0)

            settings = True
            return

    dest = parts.pop()
    dest = parts.pop()
    command_queue.append({ "device": dest, "command": message})

#
# Scan for Apple TVs and assure the ones in Config.js are found
# async def scan():
#     global config_map
#     global atv_map

#     loop = asyncio.get_event_loop()
#     atv_map = {}

#     scanning = True
#     while scanning:
#         scanning = False
#         print("Scanning for apple tvs...")
#         devices = await pyatv.scan(loop, timeout=5)
#         print("  config_map", config_map.keys())
#         if not devices:
#             print("No apple tvs found", file=sys.stderr)
#             scanning = True
#         else:
#             for atv in devices:
#                 ip = str(atv.address)
#                 atv_map[ip] = atv
#                 print("device", atv.address, atv.name)

#             print("  atv_map", atv_map.keys())

#             for key in config_map.keys():
#                 if key  in atv_map.keys():
#                     config_map[key]["appletv"] = atv_map[key]
#                 else:
#                     print("   ... key ", key, "not in atv_map")
#                     scanning = True
#                     break

#     print("Scan complete!")
#     return devices

# def get_config():
#     print("Getting global Config")
#     config = []
#     mongo = MongoClient(MONGO_HOST)
#     db = mongo["settings"]
#     collection = db.config
#     raw = collection.find_one({"_id": "config"})
#     for entry in raw["appletv"]["devices"]:
#         ip = socket.gethostbyname(entry['device']);
#         config_map[ip]= entry
#         print("  config", ip, entry['name'], entry['device'])
#         config.append(entry)

#     return config

async def main():
    global config
    global atvs
    global config_map
    global device_map
    global atv_map

    print("Getting global Config")
    mongo = MongoClient(MONGO_HOST)
    db = mongo["settings"]
    collection = db.config
    raw = collection.find_one({"_id": "config"})
    for entry in raw["appletv"]["devices"]:
        ip = socket.gethostbyname(entry['device']);
        config_map[ip]= entry
        print("entry", entry);
        print("  config", ip, entry['name'], entry['device'])
        config.append(entry)
        device_map[entry['device']] = entry
#     config =  get_config()
    # print("config_map", config_map.keys())

#     devices = await scan() # get ATVs
    loop = asyncio.get_event_loop()
    atv_map = {}

    scanning = True
    while scanning:
        scanning = False
        print("Scanning for apple tvs...")
        devices = await pyatv.scan(loop, timeout=5)
        # print("  config_map", config_map.keys())
        if not devices:
            print("No apple tvs found", file=sys.stderr)
            scanning = True
        else:
            for atv in devices:
                ip = str(atv.address)
                atv_map[ip] = atv
                print("  found device", atv.address, atv.name)

            for key in config_map.keys():
#                 print('key', key, config_map[key], atv_map[key]);
                if key  in atv_map.keys():
                    atv_map[key].set_credentials(Protocol.AirPlay, config_map[key]["credentials"]);
                    config_map[key]["appletv"] = atv_map[key]
                else:
                    print("   ... key ", key, "not in atv_map")
                    scanning = True
                    break

    print("Scan complete!")

    for device in config:
#         print(".\n")
#         print(".\n")
#         print(".\n")
#         print(".\n")
#         print(device)

#         print(".\n")
#         print(".\n")
#         print(".\n")
#         print(".\n")

#         atv = device['atv']
#         print("found", device.name, found);
        device['state'] = {
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
            "contentIdentifier": None,
            "season_number": None,
            "episode_number": None,
            "series_name": None,
        }
        try:
            app = "None"
            # print("ATV Connecting to ", device['name'])

            atv = await pyatv.connect(device['appletv'], loop)
            device['atv'] = atv
            # print("Connected to ATV")
            topic = "appletv/{}/set/command".format(device['device'])
            print("subscribe", topic)
            MQTT.subscribe(topic);
#         except Exception as err:
        finally:
            pass
#             print("Exception err {}".format(err));
#             continue

#             found['atv'] = atv
#             fn = found['device']
#             print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz found", found, fn)
#             atv_map[fn] = atv
#             atv_map[found[device]] = atv
#             atvs.append({ 
#                 "config": found,
#                 "device": device,
#                 "atv": atv, 
#                 })


    while True:
        for item in config:
            # print("item", item)
            device = item['device']
            name = item['name']
            atv = item['atv']
            conf = item
            # print("loop", name)

            app = "None"
            try:
                app = atv.metadata.app.name
                # print(app)
            except Exception:
                app = "None"
           
            power = atv.power.power_state == PowerState.On
            playing = await atv.metadata.playing()

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
                "seasonNumber": playing.season_number if hasattr(playing,'season_number') else None,
                "episodeNumber": playing.episode_number if hasattr(playing,'episode_number') else None,
                "seriesName": playing.series_name if hasattr(playing,'series_name') else None,
                "contentIdentifier": playing.content_identifier if hasattr(playing,'content_identifier') else None,
            }

#             try: 
#                 o["contentIdentifier"] = playing.content_identifier
#             finally:
#                 pass

#             try: 
#                 o["season_number"] = playing.season_number
#             finally:
#                 pass
                
#             try: 
#                 o["episode_number"] = playing.episode_number
#             finally:
#                 pass
                
#             try: 
#                 o["series_name"] = playing.series_name
#             finally:
#                 pass

#             if convert.device_state_str(playing.device_state) == "Playing":
#                 print(playing.__dict__)
#                 print("")

            if o != conf['state']:
                topic = "appletv/{}/status/{}".format(conf['device'], "info")
                # print(topic, json.dumps(o)[:40])
                MQTT.publish(topic, json.dumps(o), retain=True)
            
            for attr, value in o.items():
#                 print("attr", attr, "value", value, conf['state'][attr])
                try:
                    if value != conf["state"][attr]:
                        topic = "appletv/{}/status/{}".format(conf['device'], attr)
                        # if  name == "Office":
                        #     print(name, "publish", topic, value)
                        conf['state'][attr] = o[attr]
                        MQTT.publish(topic, value, retain=True)
                except Exception as ex:
                    try:
                        MQTT.publish(topic, value, retain=True)
                    finally:
                        pass
                    


        # process queue
#         print("process queue")
        while True:
            try:
                cmd = command_queue.pop()
                print("dequeue command", cmd)
                device = cmd['device']
                message = cmd['command']

                print("command", device, message)
                if device == "reset":
                    print("RECEIVED RESET.  EXITING...\n\n\n");
                    os._exit(0)

                atv = device_map[device]['atv']

                if message == "STOP":
                    await atv.remote_control.right()
                elif message == "MENU":
                    await atv.remote_control.menu()
                elif message == "SUSPEND":
                    await atv.remote_control.home()
                elif message == "HOME":
                    await atv.remote_control.home()
                elif message == "POWER":
                    await atv.power.turn_off()
                elif  message == "UP":
                    await atv.remote_control.up()
                elif  message == "DOWN":
                    await atv.remote_control.down()
                elif  message == "LEFT":
                    await atv.remote_control.left()
                elif  message == "RIGHT":
                    await atv.remote_control.right()
                elif  message == "SELECT":
                    await atv.remote_control.select()
                elif  message == "PAUSE":
                    await atv.remote_control.pause()
                elif  message == "PLAY":
                    await atv.remote_control.play()
                elif  message == "BEGINREWIND":
                    await atv.remote_control.skip_backward()
                elif  message == "BEGINFORWARD":
                    await atv.remote_control.skip_forward()
                else:
                    print("invalid command", message)
            except Exception:
                break
    
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("\n\npyatv-microservice.py v1.0\n\n");
    print("MQTT connecting...")
    MQTT.on_connect = on_connect
    MQTT.on_message = on_message
    try:
        ret = MQTT.connect(MQTT_HOST)
        print("MQTT connected " + str(ret))
        # client.subscribe("hubitat/#")
        MQTT.loop_start()
    except Exception as err:
        print("MQTT Connect Exception " + str(err), err)
    asyncio.get_event_loop().run_until_complete(main())


