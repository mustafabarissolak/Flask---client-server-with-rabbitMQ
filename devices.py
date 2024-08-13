import json

file_path = "snmpDevices.json"


def load_device_data():
    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []


def save_device_data(data):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


device_data = load_device_data()
