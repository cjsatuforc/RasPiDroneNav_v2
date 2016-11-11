#!python2
# -*- coding: UTF-8 -*-

"""
A module which approximates the contour (input), gives it a name
based on number of vertices and returns simplified contour with it's
vertices, area and name .

.. moduleauthor:: Michal Ciesielski <ciesielskimm@gmail.com>

"""

import cv2
import time
import imutils
import Queue
import signal
import logging
from threading import Thread
from pivideostream import PiVideoStream


class VisionSystem:
    """docstring for visionSystem"""
    def __init__(self, q1, q2):
        self.queue_MAIN_2_VS = q1
        self.queue_VS_2_STM = q2
        self.resolution = (320, 240)
        self.colorspace = 'yuv'
        self.video_stream = PiVideoStream(streamColorSpace=self.colorspace,
                                          resolution=self.resolution,
                                          framerate=60)

        self.settings = {'disp': False, 'dispThresh': False,
                         'dispContours': False, 'dispApproxContours': False,
                         'dispVertices': False, 'dispNames': False,
                         'dispCenters': False, 'dispTHEcenter': False,
                         'erodeValue': 0, 'lowerThresh': 40, 'working': True,
                         'autoMode': False, 'dispGoal': True}

        self.prevStateDisp = self.settings['disp']
        self.prevStateDispThresh = self.settings['dispThresh']

        self.objs = []

        self.classLogger = logging.getLogger('droneNav.VisionSys')

        self.working = True
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.classLogger.debug('Starting vision system.')
        self.video_stream.start()
        time.sleep(2)
        self.working = True
        self.t.start()
        return

    def stop(self):
        self.working = False
        self.t.join()
        return

    def update(self):
        while 1:
            if self.working is False:
                break

            if self.queue_MAIN_2_VS.empty():
                pass
            if not self.queue_MAIN_2_VS.empty():
                self.settings = self.queue_MAIN_2_VS.get()
                self.queue_MAIN_2_VS.task_done()

            frame = self.video_stream.read()
            frame_processed = self.process_frame(frame, self.settings)
            self.detect_shapes(frame, frame_processed)


            if self.settings['disp'] is False and self.prevStateDisp is False:
                pass
            if self.settings['disp'] is True and self.prevStateDisp is False:
                cv2.namedWindow('Frame')
                key = cv2.waitKey(1) & 0xFF
                # cv2.startWindowThread()
            elif self.settings['disp'] is True and self.prevStateDisp is True:
                key = cv2.waitKey(1) & 0xFF
                cv2.imshow('Frame', frame)
            elif self.settings['disp'] is False and self.prevStateDisp is True:
                cv2.destroyWindow('Frame')

            if self.settings['dispThresh'] is False and self.prevStateDispThresh is False:
                pass
            if self.settings['dispThresh'] is True and self.prevStateDispThresh is False:
                cv2.namedWindow('Processed')
                key = cv2.waitKey(1) & 0xFF
                # cv2.startWindowThread()
            elif self.settings['dispThresh'] is True and self.prevStateDispThresh is True:
                key = cv2.waitKey(1) & 0xFF
                cv2.imshow('Processed', frame_processed)
            elif self.settings['dispThresh'] is False and self.prevStateDispThresh is True:
                cv2.destroyWindow('Processed')

            if self.settings['dispThresh'] or self.settings['disp']:
                if key == 27:
                    self.video_stream.stop()

            self.prevStateDisp = self.settings['disp']
            self.prevStateDispThresh = self.settings['dispThresh']

            # send objects to state machine
            self.queue_VS_2_STM.put(self.objs)

        cv2.destroyAllWindows()
        self.video_stream.stop()
        self.classLogger.debug('Ending vision system.')

    def process_frame(self, fr, setts):
        """ Takes frame and processes it based on settings. """
        # frame = imutils.resize(frame, width=600)
        # fr = cv2.flip(fr, 0)
        # frame = cv2.copyMakeBorder(frame, 3, 3, 3, 3,
        #                            cv2.BORDER_CONSTANT,
        #                            value=(255, 255, 255))
        if self.colorspace == 'rgb':
            frameGray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            frameBlurred = cv2.GaussianBlur(frameGray, (7, 7), 0)
        else:
            frameBlurred = cv2.GaussianBlur(fr, (7, 7), 0)

        frameThresh = cv2.threshold(frameBlurred, setts['lowerThresh'], 255,
                                    cv2.THRESH_BINARY_INV)[1]
        frameThresh = cv2.erode(frameThresh, None,
                                iterations=setts['erodeValue'])
        frameThresh = cv2.dilate(frameThresh, None,
                                 iterations=setts['erodeValue'])
        frameThresh = cv2.copyMakeBorder(frameThresh, 3, 3, 3, 3,
                                         cv2.BORDER_CONSTANT, value=(0, 0, 0))
        frameFinal = frameThresh

        return frameFinal

    def draw_cntrs_features(self, fr, setts, obj):
        """
        Takes frame, settings, objects list and draws features (contours,
        names, vertives, centers) on frame.
        """
        if setts['dispContours']:
            cv2.drawContours(fr, [obj['contour']], -1, (255, 255, 0), 1)
        if setts['dispApproxContours']:
            cv2.drawContours(fr, [obj['approx_cnt']], -1, (0, 255, 0), 1)
        if setts['dispNames']:
            cv2.putText(fr, obj['shape'] + str(obj['approx_cnt_area']),
                        obj['center'], cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1)
        if setts['dispVertices']:
            for i in range(0, len(obj['verts'])):
                cv2.circle(fr, tuple(obj['verts'][i]), 4, (255, 100, 100), 1)
        if setts['dispCenters']:
            cv2.circle(fr, (obj['center']), 2, (50, 255, 50), 1)

    def detect_shapes(self, frameOriginal, frameProcessed):
        """
        This functiion simplifies the contour, identifies shape by name,
        unpacks vertices, computes area. Then it returns a dictionary with
        all of this data.

        :param c: Contour to be approximated.
        :type c: OpenCV2 contour.
        :returns: dictionary -- shape name, vertices, approximated contour,
        approximated area.
        :rtype: dictionary.
        """

        # hack to circumvent opencv error
        if self.colorspace == 'yuv':
            frameOriginal = frameOriginal.copy()

        # #####################################################################
        # FIND COUNTOURS
        # #####################################################################
        cnts = cv2.findContours(frameProcessed.copy(),
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        # #####################################################################
        # ANALYZE CONTOURS
        # #####################################################################

        # clear list
        self.objs = []

        for index, c in enumerate(cnts):
            verts = []
            vrt = []

            # #################################################################
            # SIMPLIFY CONTOUR
            # #################################################################
            perimeter = cv2.arcLength(c, True)
            approx_cnt = cv2.approxPolyDP(c, 0.04 * perimeter, True)

            # #################################################################
            # GET CONTOUR AREA
            # #################################################################
            approx_cnt_area = cv2.contourArea(approx_cnt)

            # #################################################################
            # GETTING THE VERTICES COORDINATES
            # #################################################################
            for i in range(0, len(approx_cnt)):
                # iterate over vertices (needs additional [0]
                vrt = []
                for j in range(0, 2):
                    vrt.append(int(approx_cnt[i][0][j]))
                verts.append(vrt)

            # #################################################################
            # NAMING THE OBJECT
            # #################################################################
            # if the shape is a triangle, it will have 3 vertices
            if len(approx_cnt) == 3:
                shape = "triangle"

            # if the shape has 4 vertices, it is either a square or
            # a rectangle
            elif len(approx_cnt) == 4:
                # compute the bounding box of the contour and use the
                # bounding box to compute the aspect ratio
                (x, y, w, h) = cv2.boundingRect(approx_cnt)
                ar = w / float(h)

                # a square will have an aspect ratio that is approximately
                # equal to one, otherwise, the shape is a rectangle
                shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

            # if the shape is a pentagon, it will have 5 vertices
            elif len(approx_cnt) == 5:
                shape = "pentagon"

            # otherwise, we assume the shape is a circle
            else:
                shape = "circle"

            # #################################################################
            # COMPUTING CENTER
            # #################################################################
            M = cv2.moments(approx_cnt)
            try:
                approx_cnt_X = int((M['m10'] / M['m00']))
                approx_cnt_Y = int((M['m01'] / M['m00']))
            except ZeroDivisionError:
                approx_cnt_X = 0
                approx_cnt_Y = 0

            obj = {'shape': shape,
                   'verts': verts,
                   'approx_cnt': approx_cnt,
                   'approx_cnt_area': approx_cnt_area,
                   'contour': c,
                   'center': (approx_cnt_X, approx_cnt_Y)}

            self.objs.append(obj)

            c = c.astype('float')
            c = c.astype('int')

            self.draw_cntrs_features(frameOriginal,
                                     self.settings,
                                     self.objs[index])

        if self.settings['dispTHEcenter']:
            cv2.circle(frameOriginal,
                       (self.resolution[0] / 2, self.resolution[1] / 2),
                       2,
                       (50, 50, 255),
                       1)

        if self.settings['dispGoal'] and bool(self.objs):
            cv2.line(frameOriginal,
                     (self.resolution[0] / 2, self.resolution[1] / 2),
                     self.objs[0]['center'],
                     (255, 0, 0),
                     2)


if __name__ == "__main__":
    try:
        q1 = Queue.Queue()
        q2 = Queue.Queue()
        vs = VisionSystem(q1, q2)
        vs.start()
        # pauses main thread in this place so it can catch
        # exceptions; otherwise try/except just ends and thread
        # is running in the background
        signal.pause()
    except KeyboardInterrupt:
        vs.stop()
        print('Keyboard Interrupt')
    except Exception as e:
        print(e)
        vs.stop()
