#!python2
# -*- coding: UTF-8 -*-

"""
A module which approximates the contour (input), gives it a name
based on number of vertices and returns simplified contour with it's
vertices, area and name .

.. moduleauthor:: Michal Ciesielski <ciesielskimm@gmail.com>

"""

import Queue
import os
import logging
import argparse
import signal
from visionsystem import VisionSystem
from cliinterface import CliInterface
from dronestatemachine import DroneStateMachine
from serialcom import SerialCom
from manualcontrol import ManualControl

stopped = False
settings = {'disp': False,
            'dispThresh': False,
            'dispContours': False,
            'dispApproxContours': False,
            'dispVertices': False,
            'dispNames': False,
            'dispCenters': False,
            'dispTHEcenter': False,
            'erodeValue': 0,
            'lowerThresh': 40,
            'working': True,
            'autoMode': False,
            'dispGoal': True}


def main():
    # #########################################################################
    # LOCAL VARS
    # #########################################################################
    main_dir = os.path.dirname(__file__)
    autoModePrev = False

    # #########################################################################
    # ARGS PARSING
    # #########################################################################
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--display", type=int, default=1,
                    help="Whether or not frames should be displayed.")
    ap.add_argument("-c", "--cli", type=int, default=1,
                    help="Whether or not curses process should start.")
    args = vars(ap.parse_args())

    # #########################################################################
    # QUEUES
    # #########################################################################
    queue_CLI_2_MAIN = Queue.Queue()
    queue_MAIN_2_VS = Queue.Queue()
    queue_MAIN_2_STM = Queue.Queue()
    queue_VS_2_STM = Queue.Queue()
    queue_STM_MAN_2_SRL = Queue.Queue()

    # #########################################################################
    # LOGS
    # #########################################################################
    logger1 = createLogger(main_dir, 'droneNav', 'log')
    logger2 = createLogger(main_dir, 'serialCom', 'logValues')

    # #########################################################################
    # OBJECTS
    # #########################################################################
    vis_sys     = VisionSystem(queue_MAIN_2_VS, queue_VS_2_STM)
    cli         = CliInterface(queue_CLI_2_MAIN, main_dir)
    man_ctrl    = ManualControl(queue_STM_MAN_2_SRL)
    drone_stm   = DroneStateMachine(queue_VS_2_STM, queue_STM_MAN_2_SRL)
    serial_port = SerialCom(queue_STM_MAN_2_SRL)

    # #########################################################################
    # STARTS
    # #########################################################################
    logger1.debug('Starting main.')
    cli.start()
    vis_sys.start()
    serial_port.start()
    drone_stm.start()
    man_ctrl.start()
    man_ctrl.connect_queue(True)

    # #########################################################################
    # MAIN LOOP
    # #########################################################################
    while 1:

        # UPDATE SETTINGS
        if not queue_CLI_2_MAIN.empty():
            settings = queue_CLI_2_MAIN.get()
            queue_CLI_2_MAIN.task_done()
        else:
            continue

        # SEND SETTINGS
        queue_MAIN_2_VS.put(settings)

        if autoModePrev is False and settings['autoMode'] is True:
            drone_stm.write(man_ctrl.read(), 'all')
            man_ctrl.connect_queue(False)
            drone_stm.connect_queue(True)
        elif autoModePrev is True and settings['autoMode'] is False:
            man_ctrl.write(drone_stm.read(), 't')
            drone_stm.connect_queue(False)
            man_ctrl.connect_queue(True)

        autoModePrev = settings['autoMode']

        if not settings['working']:
            break

    man_ctrl.stop()
    cli.stop()
    serial_port.stop()
    vis_sys.stop()
    drone_stm.stop()
    logger1.debug('Ending main.')


def createLogger(log_dir, loggerID, name):
    """
    Takes dir for log file.
    Returns logger object with formatter and file handle.
    """
    log = logging.getLogger(loggerID)
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_dir + '/' + name)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(module)s '
                                  '%(levelname)s %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stopped = True
