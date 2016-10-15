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

    def start(self):
        self.classLogger.debug('Starting serial com.')
        self.SP = serial.Serial('/dev/ttyAMA0',
                                self.BaudRate,
                                timeout=5)
        self.SP.flush()
        self.SP.flushInput()

        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while self.running:
            if self.queueSRL.empty():
                continue
            if not self.queueSRL.empty():
                self.data = self.queueSRL.get()
                self.queueSRL.task_done()
                self.SP.write(self.data)

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

        self.stop()

    def read(self):
        return self.numericals

    def clean(self):
        self.SP.flush()
        self.SP.flushInput()
        return

    def stop(self):
        self.SP.close()
        return
