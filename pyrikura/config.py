__all__ = ('Config', 'reload')

from six.moves import configparser
import os.path

Config = configparser.ConfigParser()


def reload(path):
    jpath = os.path.join
    Config.read(jpath(path, 'config.ini'))

