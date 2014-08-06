__all__ = ('Config',)

from six.moves import configparser
import os.path

Config = configparser.ConfigParser()


def reload(path):
    jpath = os.path.join
    Config.read(jpath(path, 'config.ini'))

#reload('/home/mjolnir/git/PURIKURA/config/')
reload('/Volumes/Mac2/Users/leif/pycharm/PURIKURA/config')