#!python2
# -*- coding: UTF-8 -*-

from threading import Thread, Timer
import logging
import array
import time


class DroneStateMachine:
    def __init__(self, q1, q2):
        self.possibleStates = {'onTheGround': 0,
                               'ascending': 1,
                               'rotating': 2,
                               'movingToPoint': 3,
                               'landing': 4,
                               'hovering': 5,
                               'hoveringOnPoint': 6,
                               'dummy': 99}
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
        self.n = 0
        self.interval = 0.02
        self.trust = 0
        self.timeout = 0

        self.dx = 0
        self.dy = 0
        self.dArea = 0
        self.area = 0

        self.goalX = 0
        self.goalY = 0
        self.goalArea = (0.1) * (self.resolution[0] * self.resolution[1])

        self.KPx = 0
        self.KPy = 0
        self.KPa = 0
        self.KIa = 0

        self.deadZonex = 0
        self.deadZoney = 0
        self.deadZonea = 1000

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

        self.t = None
        # self.t = Thread(target=self.update, args=())
        # self.t.daemon = True

    def start(self):
        if self.t is None:
            self.class_logger.info('Starting state machine.')
            self.set_state(self.possibleStates['onTheGround'])

            # self.t = Thread(target=self.update, args=())
            self.t = Timer(self.interval, self.update, args=())

            self.running = True
            self.t.start()
        return

    def stop(self):
        if self.t is not None:
            self.running = False
            self.t.join()
        return

    def update(self):
        if self.running is True:
            self.t = Timer(self.interval, self.update, args=())
            self.t.start()
        # #########################################################
        # GET DATA FROM VISION SYSTEM
        # #########################################################
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

                logText = '{0} - {1}: {2}'.format('OtG',
                                                  'count to 200',
                                                  self.timeout)

                self.class_logger.info(logText)

                self.timeout += 1

                if self.timeout > 200:
                    self.set_state(self.possibleStates['ascending'])
                    self.timeout = 0

            # #########################################################
            # ASCENDING
            # #########################################################
            elif self.state == self.possibleStates['ascending']:
                self.log_state_once(self.state)

                # ascend
                self.n += 1

                if self.n > 4:
                    self.pwm0 = self.pwm0 + 2
                    self.n = 0

                if self.pwm0 > 130:
                    self.pwm0 = 130

                # enough trust to change state
                if objCount == 1:
                    if self.objs[0]['shape'] == 'circle':
                        self.trust += 4
                else:
                    self.trust -= 1

                if self.trust > 40:
                    self.trust = 0
                    self.set_state(self.possibleStates['hoveringOnPoint'])

                # timeout waiting for state change
                self.timeout += 1

                if self.timeout > 100:
                    self.set_state(self.possibleStates['landing'])
                    self.timeout = 0

            # #########################################################
            # HOVERING ON POINT
            # #########################################################
            elif self.state == self.possibleStates['hoveringOnPoint']:
                self.log_state_once(self.state)

                # not seeing anything logical
                if objCount > 3 or objCount < 1:
                    pass

                # seeing 1 2 or 3 objects
                else:
                    if objCount == 1:
                        self.goalX = self.objs[0]['center'][0]
                        self.goalY = self.objs[0]['center'][1]
                        self.area = self.objs[0]['approx_cnt_area']
                    if objCount == 2:
                        self.goalX = (self.objs[0]['center'][0] +
                                      self.objs[1]['center'][0]) / 2
                        self.goalY = (self.objs[0]['center'][1] +
                                      self.objs[1]['center'][1]) / 2
                        self.area = (self.objs[0]['approx_cnt_area'] +
                                     self.objs[1]['approx_cnt_area']) / 2
                    if objCount == 3:
                        self.goalX = (self.objs[0]['center'][0] +
                                      self.objs[1]['center'][0] +
                                      self.objs[2]['center'][0]) / 3
                        self.goalY = (self.objs[0]['center'][1] +
                                      self.objs[1]['center'][1] +
                                      self.objs[2]['center'][1]) / 3
                        self.area = (self.objs[0]['approx_cnt_area'] +
                                     self.objs[1]['approx_cnt_area'] +
                                     self.objs[2]['approx_cnt_area']) / 3

                    self.dx = self.resolution[0] / 2 - self.goalX
                    self.dy = self.resolution[1] / 2 - self.goalY

                    # change the goal area for this state
                    self.goalArea = (0.03) * (self.resolution[0] * self.resolution[1])

                    # compute the diff. between the is and what is the goal
                    self.dArea = self.area - self.goalArea

                    self.deadZonex = 10
                    self.deadZoney = 10
                    self.KPx = 0.1000
                    self.KPy = 0.1360
                    self.KPa = 0.0003

                    if self.dy > 0:
                        self.pwm2 = 150 - self.KPy * (self.dy - self.deadZoney)
                    elif self.dy < 0:
                        self.pwm2 = 150 - self.KPy * (self.dy + self.deadZoney)

                    if self.dx > 0:
                        self.pwm3 = 150 - self.KPx * (self.dx - self.deadZonex)
                    elif self.dx < 0:
                        self.pwm3 = 150 - self.KPx * (self.dx + self.deadZonex)

                    if self.dy > -10 and self.dy < 10:
                        self.pwm2 = 150

                    if self.dx > -10 and self.dx < 10:
                        self.pwm3 = 150

                # self.n += 1

                # if self.n > 20:
                # if self.dArea > 0:
                self.pwm0 = self.pwm0 + self.KPa * (self.dArea)  # - self.deadZonea)
                # elif self.dArea < 0:
                    # self.pwm0 = self.pwm0 - self.KPa * (self.dArea)  # + self.deadZonea)
                    # self.n = 0

                if self.pwm0 > 130:
                    self.pwm0 = 130
                if self.pwm0 < 100:
                    self.pwm0 = 100

                logText = '{0} - {1}: {2} {3} {4} {5} {6} {7} {8}'.format('HoP',
                                                                  'objs',
                                                                  objCount,
                                                                  'dx',
                                                                  self.dx,
                                                                  'dy',
                                                                  self.dy,
                                                                  'dArea',
                                                                  self.dArea)
                self.class_logger.info(logText)

            # #########################################################
            # HOVERING
            # #########################################################
            elif self.state == self.possibleStates['hovering']:
                self.log_state_once(self.state)

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

                self.n += 1

                if self.n > 4:
                    self.pwm0 = self.pwm0 - 1
                    self.n = 0

                if self.pwm0 < 100:
                    self.pwm0 = 100

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

        if self.running is False:
            self.log_state_once.has_run = False
            self.class_logger.info('Ending state machine.')
            self.t = None

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

    def write(self, values_list, which):
        if which == 't':
            self.pwm0 = values_list[0]
            self.pwm1 = 150
            self.pwm2 = 150
            self.pwm3 = 150
            self.pwm4 = 150
            self.pwm5 = 150
        elif which == 'all':
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
        for index, v in enumerate(valueList):
            valueList[index] = max(min(v, 200), 100)
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
