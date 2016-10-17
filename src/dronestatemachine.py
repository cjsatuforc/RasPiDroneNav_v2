#!python2
# -*- coding: UTF-8 -*-

from threading import Thread, Timer
import logging
import array
import time
from serialcom import SerialCom


class DroneStateMachine:
    def __init__(self, q1, q2):
        self.possibleStates = {'onTheGround': 0, 'ascending': 1,
                               'rotating': 2, 'movingToPoint': 3,
                               'landing': 4, 'hovering': 5,
                               'hoveringOnPoint': 6, 'dummy': 99}
        self.state = self.possibleStates['dummy']
        self.running = True
        self.autoMode = False
        self.queue_VS_2_STM = q1
        self.queue_STM_MAN_2_SRL = q2
        self.queue_connected = False
        self.objs = []
        self.frequency = 50
        self.compute = False
        self.dt = 0.0
        self.resolution = (320, 240)
        self.dx = 0
        self.dy = 0
        self.n = 0

        self.log_state_once = self.run_once(self.log_state)

        # TODO: check the names below
        # throttle
        self.pwm0 = 100
        # yaw
        self.pwm1 = 150
        # pitch
        self.pwm2 = 150
        # roll
        self.pwm3 = 150
        # accessory 1
        self.pwm4 = 150
        # accessory 2
        self.pwm5 = 150

        self.values = [int(self.pwm0),
                       int(self.pwm1),
                       int(self.pwm2),
                       int(self.pwm3),
                       int(self.pwm4),
                       int(self.pwm5)]

        # logging
        self.class_logger = logging.getLogger('droneNav.StateMachine')

        self.t = Thread(target=self.update, args=())
        # self.t.daemon = True

    def start(self):
        self.class_logger.info('Starting state machine.')
        self.set_state(self.possibleStates['onTheGround'])

        self.t = Thread(target=self.update, args=())
        self.t.start()
        self.running = True
        return

    def stop(self):
        self.running = False
        self.t.join()
        return

    def update(self):
        while 1:
            if self.running is False:
                break

            # getting the objects seen by camera
            if self.queue_VS_2_STM.empty():
                self.compute = False
            else:
                self.objs = self.queue_VS_2_STM.get()
                if isinstance(self.objs, list):
                    self.compute = True
                    objCount = len(self.objs)
                else:
                    self.compute = False
                self.queue_VS_2_STM.task_done()

            if self.compute and self.queue_connected:
                # #########################################################
                # ON THE GROUND STATE
                # #########################################################
                if self.state == self.possibleStates['onTheGround']:
                    self.log_state_once(self.state)

                    # if 3 seconds from start elapsed
                    for zzz in xrange(0, 4):
                        self.class_logger.info('Ascending in: ' + str(3 - zzz))
                        time.sleep(1)

                    self.set_state(self.possibleStates['ascending'])

                # #########################################################
                # ASCENDING
                # #########################################################
                elif self.state == self.possibleStates['ascending']:
                    self.log_state_once(self.state)

                    self.n += 1

                    if self.n > 200:
                        self.pwm0 = self.pwm0 + 1
                        self.n = 0

                    if self.pwm0 > 150:
                        self.pwm0 = 150

                    # not seeing anything logical
                    if objCount > 3 or objCount < 1:
                        pass

                    # seeing 1 2 or 3 objects
                    else:
                        if objCount == 1:
                            self.dx = self.resolution[0] -self.objs[0]['center'][0]
                            self.dy = self.resolution[1] - self.objs[0]['center'][1]
                        if objCount == 2:
                            self.dx = self.resolution[0] - self.objs[0]['center'][0]
                            self.dy = self.resolution[1] - self.objs[0]['center'][1]
                        if objCount == 3:
                            self.dx = self.resolution[0] - self.objs[0]['center'][0]
                            self.dy = self.resolution[1] - self.objs[0]['center'][1]

                    logText = '{0} - {1}: {2}'.format('Ascending',
                                                      'nr of objs: ',
                                                      objCount)

                    self.class_logger.info(logText)

                # #########################################################
                # ROTATING
                # #########################################################
                elif self.state == self.possibleStates['rotating']:
                    self.log_state_once(self.state)

                # #########################################################
                # MOVING TO POINT
                # #########################################################
                elif self.state == self.possibleStates['movingToPoint']:
                    self.log_state_once(self.state)

                # #########################################################
                # LANDING
                # #########################################################
                elif self.state == self.possibleStates['landing']:
                    self.log_state_once(self.state)

                # #########################################################
                # HOVERING
                # #########################################################
                elif self.state == self.possibleStates['hovering']:
                    self.log_state_once(self.state)

                # #########################################################
                # HOVERING ON POINT
                # #########################################################
                elif self.state == self.possibleStates['hoveringOnPoint']:
                    self.log_state_once(self.state)

                # #########################################################
                # SEND DATA
                # #########################################################
                self.values = [int(self.pwm0),
                               int(self.pwm1),
                               int(self.pwm2),
                               int(self.pwm3),
                               int(self.pwm4),
                               int(self.pwm5)]
                valuesHexString = self.build_data_hex_string(self.values)
                if self.queue_connected:
                    self.queue_STM_MAN_2_SRL.put(valuesHexString)

        self.log_state_once.has_run = False
        self.class_logger.info('Ending state machine.')

    def log_state(self, state):
        if state == self.possibleStates['onTheGround']:
            logText = '{0:14s}: dt {1:2.3f}'.format('onTheGround', self.dt)
        elif state == self.possibleStates['ascending']:
            logText = '{0:14s}'.format('ascending')
        elif state == self.possibleStates['rotating']:
            logText = '{0:14s}'.format('rotating')
        elif state == self.possibleStates['movingToPoint']:
            logText = '{0:14s}'.format('movingToPoint')
        elif state == self.possibleStates['landing']:
            logText = '{0:14s}'.format('landing')
        elif state == self.possibleStates['hovering']:
            logText = '{0:14s}'.format('hovering')
        elif state == self.possibleStates['hoveringOnPoint']:
            logText = '{0:14s}'.format('hoveringOnPoint')

        self.class_logger.info(logText)
        return

    def read(self):
        return [self.pwm0, self.pwm1, self.pwm2,
                self.pwm3, self.pwm4, self.pwm5]

    def write(self, values_list):
        self.pwm0 = values_list[0]
        self.pwm1 = values_list[1]
        self.pwm2 = values_list[2]
        self.pwm3 = values_list[3]
        self.pwm4 = values_list[4]
        self.pwm5 = values_list[5]
        return

    def set_mode(self, mode):
        self.autoMode = mode
        self.queue_STM_MAN_2_SRL.queue.clear()
        self.queue_MAIN_2_STM.queue.clear()
        return

    def set_state(self, goalState):
        self.state = goalState
        self.log_state_once.has_run = False
        return

    def calculate_control(self, goalPos):
        # TODO: fill this function
        return

    def build_data_hex_string(self, valueList):
        valueList.insert(0, 0xAA)  # add preamble
        s = array.array('B', valueList).tostring()
        return s

    def connect_queue(self, b):
        self.queue_connected = b
        return

    def run_once(self, f):
        def wrapper(*args, **kwargs):
            if not wrapper.has_run:
                wrapper.has_run = True
                return f(*args, **kwargs)
        wrapper.has_run = False
        return wrapper
