# // Config File //
import configparser
import os


def create_config():
    config = configparser.ConfigParser()
    config["general"] = {
        "prefix": "!art",
        "crosspost_message": "{user} posted some art!",
        "debug": False,
    }
    config["discord"] = {
        "crosspost_channel": "channel_id",
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)


def read_config():
    """Read config.ini, returns ConfigParser object."""
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
    except Exception as e:
        raise AssertionError(f"Error reading config file: {e}")
    
    return config