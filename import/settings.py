import os
import configparser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config_auth = configparser.RawConfigParser()
config_auth.read(os.path.join(BASE_DIR, "config.ini"))

TESTING = {"running": False}
