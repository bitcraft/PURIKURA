#!/usr/bin/env python
"""
DBus service to share the arduino object
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import threading
import logging
import serial
from six.moves import queue

from twisted.internet import reactor, defer, protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.serialport import SerialPort

from tx.dbus import client, objects, error
from tx.dbus.interface import DBusInterface, Method

from pyrikura.config import Config


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus.arduino")

# dbus config
bus_name = Config.get('camera', 'dbus-name') + '.arduino'
bus_path = Config.get('camera', 'dbus-path') + '/arduino'


class Arduino(LineReceiver):
    """
    protocol:

    0x01: trigger
    0x80: set servo
    """
    def __init__(self, session):
        logger.debug('new arduino')
        self.session = session
        self.lock = threading.Lock()

    def process(self, cmd, arg):
        logger.debug('processing for arduino: %s %s', cmd, arg)
        if cmd == 1 and arg == 2:
            self.session.start()

    def sendCommand(self, cmd, arg):
        logger.debug('sending to arduino: %s %s', cmd, arg)
        data = chr(cmd) + chr(arg)
        self.transport.write(data)

    def lineReceived(self, data):
        logger.debug('got serial data %s', data)
        try:
            cmd, arg = [int(i) for i in data.split()]
            logger.debug('got command %s %s', cmd, arg)
            self.process(cmd, arg)
        except ValueError:
            logger.debug('unable to parse: %s', data)
            raise


class ServoServiceProtocol(LineReceiver):
    def lineReceived(self, data):
        logger.debug('got remote data %s', data)
        value = None

        try:
            value = int(data)
        except ValueError:
            logger.debug('cannot process data %s', data)

        if value == -1:
            self.transport.loseConnection()
            return

        else:
            try:
                self.factory.arduino.sendCommand(0x80, value)
            except:
                logger.debug('problem communicating with arduino')
                raise


class ServoServiceFactory(protocol.ServerFactory):
    protocol = ServoServiceProtocol

    def __init__(self, arduino):
        self._arduino = arduino

    @property
    def arduino(self):
        return self._arduino


class ArduinoHandler(object):
    def __init__(self):
        self.queue = queue.Queue(maxsize=4)
        self.lock = threading.Lock()
        self.thread = None

    def set_camera_tilt(self, value):
        """ Set camera tilt

        TODO: some kind of smoothing.
        """
        def send_message():
            while 1:
                try:
                    logger.debug('waiting for value...')
                    _value = self.queue.get(timeout=1)
                except queue.Empty:
                    logger.debug('thread timeout')
                    break
                else:
                    logger.debug('sending %s', str(_value))
                    try:
                        #write to serial port
                        #conn.send(str(_value) + '\r\n')
                        self.queue.task_done()
                    except:
                        break

            logger.debug('closing connection')
            try:
                #conn.send(str(-1) + '\r\n')
            except:
                pass

            logger.debug('end of thread')
            self.thread = None
            return

        try:
            logger.debug('adding value to arduino queue')
            self.queue.put(value, block=False)

        except queue.Full:
            logger.debug('arduino queue is full')
            try:
                self.queue.get()
                self.queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                logger.debug('got some error with arduino queue')
                pass

        if self.thread is None:
            logger.debug('starting socket thread')
            self.thread = threading.Thread(target=send_message)
            self.thread.daemon = True
            self.thread.start()


class ArduinoService(objects.DBusObject):
    """ Sharing of arduino with a 'simple' api
    """
    iface = DBusInterface(bus_name,
                          Method('open', returns='b'),
                          Method('close', returns='b'),
                          Method('reset', returns='b'),
                          Method('set_tilt', arguments='i', returns='b'))

    dbusInterfaces = [iface]

    def __init__(self, bus_path):
        logger.debug('starting photobooth service...')
        super(ArduinoService, self).__init__(bus_path)
        self._arduino_lock = threading.Lock()
        self._arduino_handler = None

    def _open(self):
        """ Open the arduino (internal use only)
        """
        with self._arduino_lock:
            self._arduino_handler = ArduinoHandler()
        return True

    def _close(self):
        """ Close the arduino (internal use only)
        """
        with self._arduino_lock:
            self._arduino_handler = None
        return True

    def _reset(self):
        """ Reset arduino by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the arduino...')
        with self._arduino_lock:
            return self._close_arduino() and self._open_arduino()

    def dbus_open(self):
        """ Open the arduino for use

        Safe to be called more that once or while arduino is already open
        """
        return self._open_arduino()

    def dbus_close(self):
        """ Close the arduino

        Safe to be called more that once or while arduino is already closed
        """
        return self._close_arduino()

    def dbus_reset(self):
        """ Reset arduino by closing and opening it again
        """
        return self._reset()

    def dbus_set_tilt(self, value):
        """ Set camera tilt

        Uses the arduino for communications with servo.

        Value must be 0 or greater, but less or equal to 180.

        TODO: some kind of smoothing.
        """
        with self._arduino_lock:
            return self._arduino_handler.set_tilt(value)


@defer.inlineCallbacks
def main():
    logger.debug('exporting arduino dbus interface...')
    try:
        conn = yield client.connect(reactor)
        conn.exportObject(ArduinoService(bus_path))
        yield conn.requestBusName(bus_name)
    except error.DBusException, e:
        logger.error('failed to export arduino dbus interface')
        reactor.stop()


if __name__ == '__main__':
    arduino = Arduino()

    try:
        s = SerialPort(arduino,
                       Config.get('arduino', 'port'),
                       reactor,
                       baudrate=Config.getint('arduino', 'baudrate'))
    except serial.serialutil.SerialException:
        raise

    reactor.callWhenRunning(main)
    reactor.run()