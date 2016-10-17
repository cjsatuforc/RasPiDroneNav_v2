#!python2
# -*- coding: UTF-8 -*-

from threading import Thread
import serial
import logging


class SerialCom():
    """docstring for CLInfo"""
    def __init__(self, q):
        self.BaudRate = 115200
        self.running = True
        self.numericals = []
        self.queueSRL = q
        self.data = 'a\n'

        self.classLogger = logging.getLogger('droneNav.SerialCom')
        self.valuesLogger = logging.getLogger('serialCom.SerialCom')

        self.t = Thread(target=self.update, args=())

    def start(self):
        self.classLogger.debug('Starting serial com.')
        self.SP = serial.Serial('/dev/ttyAMA0',
                                self.BaudRate,
                                timeout=5)

        while self.SP.is_open is False:
            try:
                self.SP.open()
            except serial.SerialException:
                pass

        self.SP.flush()
        self.SP.flushInput()

        self.t = Thread(target=self.update, args=())
        # self.t.daemon = True
        self.t.start()
        return self

    def stop(self):
        self.running = False
        # join means wait here for the thread to end
        self.t.join()
        return

    def update(self):
        while 1:
            if self.running is False:
                break

            if self.queueSRL.empty():
                continue
            if not self.queueSRL.empty():
                self.data = self.queueSRL.get()
                self.queueSRL.task_done()
                try:
                    self.SP.write(self.data)
                except:
                    continue

                try:
                    logText = '{0}:{1}:{2}:{3}:{4}:{5}:{6}'.format(ord(self.data[0]),
                                                                   ord(self.data[1]),
                                                                   ord(self.data[2]),
                                                                   ord(self.data[3]),
                                                                   ord(self.data[4]),
                                                                   ord(self.data[5]),
                                                                   ord(self.data[6])
                                                                   )
                    self.valuesLogger.info(logText)
                    pass
                except:
                    pass

        self.SP.close()
        self.classLogger.debug('Ending serial com.')

    def read(self):
        return self.numericals

    def clean(self):
        self.SP.flush()
        self.SP.flushInput()
        return
