import configparser
import os


config = configparser.ConfigParser()

config_files = [
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../config/config.default.ini'),
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../config/config.ini'),
]

# read files

config.read(config_files)
