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
        data = [170, 100, 150, 150, 150, 150, 150]
        dataPrev = list(data)
        dataChange = True

        while 1:
            if self.running is False:
                break

            # if there is no data in queue just jump to next iter
            if self.queueSRL.empty():
                continue
            # if theres is data in queue try to send and log it
            if not self.queueSRL.empty():
                data = self.queueSRL.get()
                self.queueSRL.task_done()

                if data == dataPrev:
                    dataChange = False
                else:
                    dataChange = True

                if dataChange:
                    try:
                        self.SP.write(data)
                    except:
                        continue

                # remember previous data
                dataPrev = list(data)

                # log the values
                try:
                    logText = '{0}:{1}:{2}:{3}:{4}:{5}:{6}'.format(ord(data[0]),
                                                                   ord(data[1]),
                                                                   ord(data[2]),
                                                                   ord(data[3]),
                                                                   ord(data[4]),
                                                                   ord(data[5]),
                                                                   ord(data[6])
                                                                   )
                    self.valuesLogger.info(logText)
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
