from six.moves import configparser
import os.path


kiosk = configparser.ConfigParser()
project = configparser.ConfigParser()
service = configparser.ConfigParser()


def load(path):
    jpath = os.path.join
    kiosk.read(jpath(path, 'kiosk.ini'))
    project.read(jpath(path, 'project.ini'))
    service.read(jpath(path, 'service.ini'))
