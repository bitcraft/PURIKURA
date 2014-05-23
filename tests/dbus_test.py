import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

from pyrikura.config import Config
import dbus
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus.test")

# specific to the camera system i use!
dbus_name = Config.get('camera', 'dbus-name')
dbus_path = Config.get('camera', 'dbus-path')


try:
    bus = dbus.SessionBus()
    pb_obj = bus.get_object(dbus_name, dbus_path)
    iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)
except dbus.exceptions.DBusException:
    logger.error('cannot find dbus service')
    raise


iface.open_camera()
iface.capture_preview()
iface.capture_image()
iface.download_preview()
iface.close_camera()
