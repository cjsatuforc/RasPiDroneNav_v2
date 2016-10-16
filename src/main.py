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
from serialcom import SerialCom
from cliinterface import CliInterface

stopped = False

settings = {'disp': False, 'dispThresh': False,
            'dispContours': False, 'dispApproxContours': False,
            'dispVertices': False, 'dispNames': False,
            'dispCenters': False, 'dispTHEcenter': False,
            'erodeValue': 0, 'lowerThresh': 40, 'working': True,
            'autoMode': False}


def main():
    # try:
    main_dir = os.path.dirname(__file__)

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
    queue_STM_2_SRL = Queue.Queue()

    # #########################################################################
    # LOGS
    # #########################################################################
    logger1 = createLogger(main_dir, 'droneNav', 'log')
    logger2 = createLogger(main_dir, 'serialCom', 'logValues')

    # #########################################################################
    # OBJECTS
    # #########################################################################
    vis_sys = VisionSystem(queue_MAIN_2_VS, queue_VS_2_STM)
    serial_port = SerialCom(queue_STM_2_SRL)
    cli = CliInterface(queue_CLI_2_MAIN, main_dir)

    # #########################################################################
    # STARTS
    # #########################################################################
    logger1.debug('Starting main.')
    vis_sys.start()
    serial_port.start()
    if args['cli'] > 0:
        cli.start()

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

        if not settings['working']:
            break

    serial_port.stop()
    vis_sys.stop()
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stopped = True
