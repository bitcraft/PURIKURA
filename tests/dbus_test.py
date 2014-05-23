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


print iface.open_camera()
print iface.capture_preview()
print iface.capture_image()
print iface.download_preview()
print iface.close_camera()
