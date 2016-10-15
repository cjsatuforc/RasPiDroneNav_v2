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
from visionsystem import VisionSystem
from serialcom import SerialCom
from cliinterface import CliInterface


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
    queueOBJS = Queue.Queue()
    queueSRL = Queue.Queue()
    queueCLI = Queue.Queue()

    # #########################################################################
    # LOGS
    # #########################################################################
    logger1 = createLogger(main_dir, 'droneNav', 'log')
    logger2 = createLogger(main_dir, 'serialCom', 'logValues')

    # #########################################################################
    # OBJECTS
    # #########################################################################
    vis_sys = VisionSystem(queueOBJS)
    serial_port = SerialCom(queueSRL)
    cli = CliInterface(queueCLI, main_dir)

    # #########################################################################
    # STARTS
    # #########################################################################
    vis_sys.start()
    serial_port.start()
    if args['cli'] > 0:
        cli.start()

    # except Exception as e:
    #     print(e)
    #     cli.stop()
    #     vis_sys.stop()
    #     serial_port.stop()


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
        main()
