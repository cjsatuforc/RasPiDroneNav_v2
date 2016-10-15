#!python2
# -*- coding: UTF-8 -*-

from unicurses import *
from threading import Thread
import os
import ConfigParser
import logging


class CliInterface:
    """ Class being the console line user interface. """
    def __init__(self, q, main_dir):
        self.stdscr = initscr()
        keypad(self.stdscr, True)
        curs_set(False)
        timeout(-1)  # -1 means infinity; 0 means no waiting
        cbreak()
        start_color()
        noecho()
        self.max_y, self.max_x = getmaxyx(self.stdscr)
        self.window = newwin(self.max_y, self.max_x, 0, 0)

        self.queueCLI = q

        self.running = True
        self.keyPressed = 0

        self.settings = {'dispThresh': False, 'dispContours': False,
                         'dispVertices': False, 'dispNames': False,
                         'dispCenters': False, 'dispTHEcenter': False,
                         'erodeValue': 0, 'lowerThresh': 40, 'working': True,
                         'autoMode': False}

        # configuration parser
        self.main_dir = main_dir
        self.configFilePath = (self.main_dir + '/config.ini')
        self.configPars = ConfigParser.ConfigParser()
        self.configExists = False

        # logging
        self.class_logger = logging.getLogger('droneNav.CLI')

        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.class_logger.debug('Starting console interface.')
        # create or load config file
        self.initConfig(self.configPars, self.configFilePath, self.settings)

        if self.configExists:
            self.class_logger.debug('The config.ini does exist; reading.')
            self.readConfig(self.configPars,
                            self.configFilePath,
                            self.settings)
        else:
            self.class_logger.debug('The config file doesnt exist; writing.')
            self.writeConfig(self.configPars,
                             self.configFilePath,
                             self.settings)

        # start the thread
        self.t.start()
        return self

    def stop(self):
        self.running = False
        return

    def update(self):
        while self.running:
            # wrefresh(window)
            self.printData()

            self.keyPressed = wgetch(self.window)
            # ESCAPE
            if self.keyPressed == 27:
                self.settings['working'] = not self.settings['working']
                wmove(self.stdscr, self.max_y, self.max_x)
                waddstr(self.window, '\nESC interrupt.\n', A_BOLD)
                wgetch(self.window)
                self.running = False
            elif self.keyPressed == ord('q'):
                self.settings['dispThresh'] = not self.settings['dispThresh']
            elif self.keyPressed == ord('w'):
                self.settings['dispContours'] = not self.settings['dispContours']
            elif self.keyPressed == ord('e'):
                self.settings['dispVertices'] = not self.settings['dispVertices']
            elif self.keyPressed == ord('r'):
                self.settings['dispNames'] = not self.settings['dispNames']
            elif self.keyPressed == ord('t'):
                self.settings['dispCenters'] = not self.settings['dispCenters']
            elif self.keyPressed == ord('y'):
                self.settings['dispTHEcenter'] = not self.settings['dispTHEcenter']
            elif self.keyPressed == ord('a'):
                self.settings['lowerThresh'] = self.settings['lowerThresh'] + 2
                if self.settings['lowerThresh'] > 255:
                    self.settings['lowerThresh'] = 255
            elif self.keyPressed == ord('z'):
                self.settings['lowerThresh'] = self.settings['lowerThresh'] - 2
                if self.settings['lowerThresh'] < 0:
                    self.settings['lowerThresh'] = 0
            elif self.keyPressed == ord('s'):
                self.settings['erodeValue'] = self.settings['erodeValue'] + 1
                if self.settings['erodeValue'] > 255:
                    self.settings['erodeValue'] = 255
            elif self.keyPressed == ord('x'):
                self.settings['erodeValue'] = self.settings['erodeValue'] - 1
                if self.settings['erodeValue'] < 0:
                    self.settings['erodeValue'] = 0
            elif self.keyPressed == ord('p'):
                self.writeConfig(self.configPars, self.configFilePath, self.settings)
            elif self.keyPressed == ord('o'):
                self.readConfig(self.configPars, self.configFilePath, self.settings)
            elif self.keyPressed == ord('m'):
                self.settings['autoMode'] = not self.settings['autoMode']

            # TODO: add some failsafe here that will shutdown the drone


            # it puts the data in queueCLI after pressing button because
            # it is a blocking getch() (timeout(-1))
            self.queueCLI.put(self.settings)

        endwin()
        self.t.join()

    def write(self, dataIn):
        self.settings = dataIn

    def read(self):
        return self.settings

    def printData(self):
        wclear(self.window)
        box(self.window)
        wmove(self.window, 0, 1)
        waddstr(self.window, 'Drone navigation - vision based.\n', A_BOLD)
        wmove(self.window, 1, 1)
        waddstr(self.window, '\n')
        wmove(self.window, 2, 1)
        waddstr(self.window, 'Parameters of the vision processing:\n', A_BOLD)
        wmove(self.window, 3, 1)
        waddstr(self.window, 'Display mask     <q>: {0} \n'.
                             format(self.settings['dispThresh']))
        wmove(self.window, 4, 1)
        waddstr(self.window, 'Display contours <w>: {0} \n'.
                             format(self.settings['dispContours']))
        wmove(self.window, 5, 1)
        waddstr(self.window, 'Display vertices <e>: {0} \n'.
                             format(self.settings['dispVertices']))
        wmove(self.window, 6, 1)
        waddstr(self.window, 'Display names    <r>: {0} \n'.
                             format(self.settings['dispNames']))
        wmove(self.window, 7, 1)
        waddstr(self.window, 'Display centers    <t>: {0} \n'.
                             format(self.settings['dispCenters']))
        wmove(self.window, 8, 1)
        waddstr(self.window, 'Display the center    <y>: {0} \n'.
                             format(self.settings['dispTHEcenter']))
        wmove(self.window, 9, 1)
        waddstr(self.window, 'Threshold      <a,z>: {0} - 255\n'.
                             format(self.settings['lowerThresh']))
        wmove(self.window, 10, 1)
        waddstr(self.window, 'Erode          <s,x>: {0}\n'.
                             format(self.settings['erodeValue']))
        wmove(self.window, 12, 1)
        waddstr(self.window, 'Store values to config.ini   <p>\n')
        wmove(self.window, 13, 1)
        waddstr(self.window, 'Restore values from config.ini   <o>\n')
        wmove(self.window, 16, 1)
        waddstr(self.window, 'Process working     : {0} \n'.
                             format(self.settings['working']))
        wmove(self.window, 16, 1)
        waddstr(self.window, 'Auto mode     : {0} \n'.
                             format(self.settings['autoMode']))

    def initConfig(self, cfg, path, setts):
        """
        Check if config.ini exists, fill cfg object, if not exists create.
        """
        if os.path.isfile(self.configFilePath):
            self.configExists = True
        else:
            self.configExists = False

        cfg.add_section('VisionParams')
        # append all the dict in the config
        for key in setts:
            cfg.set('VisionParams', key, str(setts[key]))

        # Python3 way to do that
        # cfg.read_dict({'VisionParams': setts})

        if not self.configExists:
            self.writeConfig(cfg, path, setts)
            self.configExists = True

    def readConfig(self, cfg, path, setts):
        if self.configExists:
            self.class_logger.debug('Reading config file.')
            cfg.read('config.ini')

            setts['dispThresh']    = cfg.getboolean('VisionParams', 'dispThresh')
            setts['dispContours']  = cfg.getboolean('VisionParams', 'dispContours')
            setts['dispVertices']  = cfg.getboolean('VisionParams', 'dispVertices')
            setts['dispNames']     = cfg.getboolean('VisionParams', 'dispNames')
            setts['dispCenters']   = cfg.getboolean('VisionParams', 'dispCenters')
            setts['dispTHEcenter'] = cfg.getboolean('VisionParams', 'dispTHEcenter')
            setts['erodeValue']    = cfg.getint('VisionParams', 'erodeValue')
            setts['lowerThresh']   = cfg.getint('VisionParams', 'lowerThresh')
        else:
            self.class_logger.debug('Tried to read config but file doesnt exist.')

    def writeConfig(self, cfg, path, setts):
        self.class_logger.debug('Writing config file.')

        cfg.remove_section('VisionParams')
        cfg.add_section('VisionParams')
        # append all the dict in the config
        for key in setts:
            if isinstance(setts[key], bool):
                cfg.set('VisionParams', key, str(setts[key]).lower())
            elif isinstance(setts[key], int):
                cfg.set('VisionParams', key, str(setts[key]))

        configFile = open(path, 'w')
        cfg.write(configFile)
        configFile.close()

        self.configExists = True


if __name__ == "__main__":
    cli = CliInterface()
    cli.start()
