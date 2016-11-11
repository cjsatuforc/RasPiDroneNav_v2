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

        self.settings = {'disp': False,
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
        self.configPars = ConfigParser.ConfigParser()
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

        self.running = True
        # start the thread
        self.t.start()
        return self

    def stop(self):
        self.running = False
        self.t.join()
        return

    def update(self):
        while 1:
            if self.running is False:
                break

            # wrefresh(window)
            self.printData()

            # BLOCKED IN THIS PLACED UNTIL KEY PRESSED
            self.keyPressed = wgetch(self.window)


            # ESCAPE
            if self.keyPressed == 27:
                self.settings['working'] = not self.settings['working']
                break
            # 1
            elif self.keyPressed == ord('1'):
                self.settings['disp'] = not self.settings['disp']
            # 2
            elif self.keyPressed == ord('2'):
                self.settings['dispThresh'] = not self.settings['dispThresh']
            # Q
            elif self.keyPressed == ord('q'):
                self.settings['dispApproxContours'] = not self.settings['dispApproxContours']
            # W
            elif self.keyPressed == ord('w'):
                self.settings['dispContours'] = not self.settings['dispContours']
            # E
            elif self.keyPressed == ord('e'):
                self.settings['dispVertices'] = not self.settings['dispVertices']
            # R
            elif self.keyPressed == ord('r'):
                self.settings['dispNames'] = not self.settings['dispNames']
            # T
            elif self.keyPressed == ord('t'):
                self.settings['dispCenters'] = not self.settings['dispCenters']
            # Y
            elif self.keyPressed == ord('y'):
                self.settings['dispTHEcenter'] = not self.settings['dispTHEcenter']
            # A
            elif self.keyPressed == ord('a'):
                self.settings['lowerThresh'] = self.settings['lowerThresh'] + 2
                if self.settings['lowerThresh'] > 255:
                    self.settings['lowerThresh'] = 255
            # Z
            elif self.keyPressed == ord('z'):
                self.settings['lowerThresh'] = self.settings['lowerThresh'] - 2
                if self.settings['lowerThresh'] < 0:
                    self.settings['lowerThresh'] = 0
            # S
            elif self.keyPressed == ord('s'):
                self.settings['erodeValue'] = self.settings['erodeValue'] + 1
                if self.settings['erodeValue'] > 255:
                    self.settings['erodeValue'] = 255
            # X
            elif self.keyPressed == ord('x'):
                self.settings['erodeValue'] = self.settings['erodeValue'] - 1
                if self.settings['erodeValue'] < 0:
                    self.settings['erodeValue'] = 0
            # P
            elif self.keyPressed == ord('p'):
                self.writeConfig(self.configPars, self.configFilePath, self.settings)
            # O
            elif self.keyPressed == ord('o'):
                self.readConfig(self.configPars, self.configFilePath, self.settings)
            # M
            elif self.keyPressed == ord('m'):
                self.settings['autoMode'] = not self.settings['autoMode']
            # N
            elif self.keyPressed == ord('n'):
                self.settings['dispGoal'] = not self.settings['dispGoal']

            # it puts the data in queueCLI after pressing button because
            # it is a blocking getch() (timeout(-1))
            self.queueCLI.put(self.settings)

        self.queueCLI.put(self.settings)
        endwin()
        self.class_logger.debug('Ending console interface.')

    def write(self, dataIn):
        self.settings = dataIn

    def read(self):
        return self.settings

    def printData(self):
        wclear(self.window)
        box(self.window)
        wmove(self.window, 0, 1)
        waddstr(self.window, '{0:<36}'.format('Parameters of the vision processing'), A_BOLD)
        wmove(self.window, 1, 1)
        waddstr(self.window, '\n')
        wmove(self.window, 2, 1)
        waddstr(self.window,
                '{0:<36}'.format('Parameters of the vision processing'),
                A_BOLD)

        wmove(self.window, 3, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display approximated contours',
                                          '<q>',
                                          self.settings['dispApproxContours']))

        wmove(self.window, 4, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display contours',
                                          '<w>',
                                          self.settings['dispContours']))

        wmove(self.window, 5, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display vertices',
                                          '<e>',
                                          self.settings['dispVertices']))

        wmove(self.window, 6, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display names',
                                          '<r>',
                                          self.settings['dispNames']))

        wmove(self.window, 7, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display centers',
                                          '<t>',
                                          self.settings['dispCenters']))

        wmove(self.window, 8, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display the center',
                                          '<y>',
                                          self.settings['dispTHEcenter']))

        wmove(self.window, 9, 1)
        waddstr(self.window,
                '{0:<34}{1} : {2:>3}-255'.format('Threshold',
                                                 '<a,z>',
                                                 self.settings['lowerThresh']))

        wmove(self.window, 10, 1)
        waddstr(self.window,
                '{0:<34}{1} : {2:>3}'.format('Erode',
                                             '<s,x>',
                                             self.settings['erodeValue']))

        wmove(self.window, 12, 1)
        waddstr(self.window,
                '{0:<36}{1}'.format('Store values to config.ini',
                                    '<p>'))

        wmove(self.window, 13, 1)
        waddstr(self.window,
                '{0:<36}{1}'.format('Restore values to config.ini',
                                    '<o>'))

        wmove(self.window, 16, 1)
        waddstr(self.window,
                '{0:<36}{1}'.format('Process working',
                                    self.settings['working']))

        wmove(self.window, 16, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Auto mode',
                                          '<m>',
                                          self.settings['autoMode']))

        wmove(self.window, 17, 1)
        waddstr(self.window,
                '{0:<36}{1} : {2}'.format('Display goal',
                                    '<n>',
                                    self.settings['dispGoal']))

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
