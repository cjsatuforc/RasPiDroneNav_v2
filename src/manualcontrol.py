#!python2
# -*- coding: UTF-8 -*-

"""
A module for manual controlling the drone with keyboard.
Keys used:
    E,D,S,F,I,K,J,L,X,1,2

.. moduleauthor:: Michal Ciesielski <ciesielskimm@gmail.com>

"""

import pygame
import array
import Queue
from threading import Thread


class ManualControl(object):
    """Class which lets control drone manually."""
    def __init__(self, q):

        self.queue_STM_MAN_2_SRL = q

        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((100, 100))
        pygame.display.set_caption('Controls test for drone.')
        pygame.mouse.set_visible(1)

        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((200, 200, 200))

        self.throttle = 1.0
        self.working = True

        self.stepUP = 50
        self.stepDOWN = 50

        self.pwm0 = self.pwm0_neutral = 100
        self.pwm1 = self.pwm1_neutral = 150
        self.pwm2 = self.pwm2_neutral = 150
        self.pwm3 = self.pwm3_neutral = 150
        self.pwm4 = self.pwm4_neutral = 150
        self.pwm5 = self.pwm5_neutral = 150

        self.pwm4_State = 0
        self.pwm5_State = 0

        self.queue_connected = True

        self.t = Thread(target=self.update, args=())

    def start(self):
        self.t.start()
        return

    def stop(self):
        self.working = False
        self.t.join()
        return

    def update(self):
        while 1:
            if not self.working:
                break

            e = pygame.event.get()
            t = self.handle_input(e)

            if t is False:
                pass

        pygame.quit()

    def build_data_hex_string(self, valueList):
        valueList.insert(0, 0xAA)  # add preamble
        s = array.array('B', valueList).tostring()
        return s

    def connect_queue(self, b):
        self.queue_connected = b
        return

    def read(self):
        return [self.pwm0, self.pwm1, self.pwm2,
                self.pwm3, self.pwm4, self.pwm5]

    def write(self, values_list, which):
        if which == 'n':
            self.pwm0 = 100
            self.pwm1 = 150
            self.pwm2 = 150
            self.pwm3 = 150
            self.pwm4 = 150
            self.pwm5 = 150
        elif which == 't':
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

    def handle_input(self, events):

        for event in events:
            if event.type == pygame.QUIT:
                pass

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHTBRACKET:
                self.throttle = self.throttle + 0.1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFTBRACKET:
                self.throttle = self.throttle - 0.1

            if self.throttle > 1:
                self.throttle = 1
            elif self.throttle < 0.1:
                self.throttle = 0.1

            # keys pressed

            # throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                # self.pwm0 = self.pwm0_neutral + self.stepUP * self.throttle
                self.pwm0 = self.pwm0 + 1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                # self.pwm0 = self.pwm0_neutral - self.stepDOWN * self.throttle
                self.pwm0 = self.pwm0 - 1

            if self.pwm0 < 100:
                self.pwm0 = 100
            elif self.pwm0 > 200:
                self.pwm0 = 200

            # safety switch - throttle full down
            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                self.pwm0 = 100
                self.pwm1 = 150
                self.pwm2 = 150
                self.pwm3 = 150
                self.pwm4 = 150
                self.pwm5 = 150

            # rest of dofs
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                self.pwm1 = self.pwm1_neutral + self.stepUP * self.throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                self.pwm1 = self.pwm1_neutral - self.stepDOWN * self.throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.pwm2 = self.pwm2_neutral + self.stepUP * self.throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                self.pwm2 = self.pwm2_neutral - self.stepDOWN * self.throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                self.pwm3 = self.pwm3_neutral + self.stepUP * self.throttle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                self.pwm3 = self.pwm3_neutral - self.stepDOWN * self.throttle

            # keys not pressed
            # if event.type == pygame.KEYUP and event.key == pygame.K_e:
                # self.pwm0 = self.pwm0_neutral
            # if event.type == pygame.KEYUP and event.key == pygame.K_d:
                # self.pwm0 = self.pwm0_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_s:
                self.pwm1 = self.pwm1_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_f:
                self.pwm1 = self.pwm1_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_i:
                self.pwm2 = self.pwm2_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_k:
                self.pwm2 = self.pwm2_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_j:
                self.pwm3 = self.pwm3_neutral
            if event.type == pygame.KEYUP and event.key == pygame.K_l:
                self.pwm3 = self.pwm3_neutral

            # accessories
            if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                self.pwm4_State = self.pwm4_State + 1
                if self.pwm4_State > 1:
                    self.pwm4_State = -1
            if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                self.pwm5_State = self.pwm5_State + 1
                if self.pwm5_State > 1:
                    self.pwm5_State = -1

            self.pwm4 = self.pwm4_neutral + self.pwm4_State * self.stepDOWN
            self.pwm5 = self.pwm5_neutral + self.pwm5_State * self.stepDOWN

            # closing app
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print('Stopped by user.')
                return False

        values = [int(self.pwm0),
                  int(self.pwm1),
                  int(self.pwm2),
                  int(self.pwm3),
                  int(self.pwm4),
                  int(self.pwm5)]
        valuesHexString = self.build_data_hex_string(values)

        if self.queue_connected:
            self.queue_STM_MAN_2_SRL.put(valuesHexString)

        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()
        self.clock.tick(50)


if __name__ == "__main__":
    q = Queue.Queue()
    ctrl = ManualControl(q)
    ctrl.start()
