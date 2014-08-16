__all__ = ('Config',)

#root = '/home/mjolnir/git/PURIKURA'
root = '/Volumes/Mac2/Users/leif/pycharm/PURIKURA'

from six.moves import configparser
import os.path

Config = configparser.ConfigParser()


def reload(path):
    jpath = os.path.join
    Config.read(jpath(path, 'config.ini'))

reload(os.path.join(root, 'config/'))
