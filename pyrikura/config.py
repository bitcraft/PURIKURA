__all__ = ('Config', 'reload')

from six.moves import configparser
import os.path

Config = None


def reload(path):
    global Config

    Config = configparser.ConfigParser()
    jpath = os.path.join
    Config.read(jpath(path, 'config.ini'))

