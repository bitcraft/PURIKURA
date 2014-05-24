__author__ = 'Leif'

@dbus.service.method(bus_name, in_signature='i', out_signature='b')
    def set_camera_tilt(self, value):
        """ Set camera tilt

        Uses the arduino for communications with servo.

        Value must be 0 or greater, but less or equal to 180.

        TODO: some kind of smoothing.
        """
        def send_serial():
            while 1:
                try:
                    _value = self._arduino_queue.get(timeout=1)
                except queue.Empty:
                    break
                with self._arduino_lock:
                    self._arduino_conn.sendCommand(0x80, int(_value))
                self._arduino_queue.task_done()
            self._arduino_thread = None

        try:
            self._arduino_queue.put(value, block=False)
        except queue.Full:
            try:
                self._arduino_queue.get()
                self._arduino_queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                pass

        if self._arduino_thread is None:
            self._arduino_thread = threading.Thread(target=send_serial)
            self._arduino_thread.start()#