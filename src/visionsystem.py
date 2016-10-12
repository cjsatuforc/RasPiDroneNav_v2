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
from threading import Thread
from pivideostream import PiVideoStream


class VisionSystem:
    """docstring for visionSystem"""
    def __init__(self, q):
        self.queueOBJS = q
        self.resolution = (320, 240)
        self.video_stream = PiVideoStream(self.resolution, 60)
        self.settings = {'dispThresh': False, 'dispContours': False,
                         'dispVertices': False, 'dispNames': False,
                         'dispCenters': False, 'dispTHEcenter': False,
                         'erodeValue': 0, 'lowerThresh': 40, 'working': True,
                         'autoMode': False}
        self.objs = []

        self.working = True
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.video_stream.start()
        time.sleep(2)
        self.t.start()
        return True

    def stop(self):
        self.working = False

    def update(self):
        while self.working:
            frame = self.video_stream.read()
            frame_processed = self.process_frame(frame, self.settings)
            self.detect_shapes(frame_processed)

            cv2.imshow('Frame', frame)
            cv2.imshow('Processed', frame_processed)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:
                self.video_stream.stop()
                self.working = False

            # send objects to state machine
            self.queueOBJS.put(self.objs)

        if not self.working:
            self.t.join()

    def process_frame(self, fr, setts):
        """ Takes frame and processes it based on settings. """
        # frame = imutils.resize(frame, width=600)
        fr = cv2.flip(fr, 0)
        # frame = cv2.copyMakeBorder(frame, 3, 3, 3, 3,
        #                            cv2.BORDER_CONSTANT,
        #                            value=(255, 255, 255))
        frameGray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        # frameBlurred = cv2.GaussianBlur(frameGray, (5, 5), 0)
        frameThresh = cv2.threshold(frameGray, setts['lowerThresh'], 255,
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
            cv2.drawContours(fr, [obj['approxPerimeter']], -1, (0, 255, 0), 1)
        if setts['dispNames']:
            cv2.putText(fr, obj['shapeName'] + str(obj['approxPerimeterArea']),
                        obj['center'], cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1)
        if setts['dispVertices']:
            for i in range(0, len(obj['verts'])):
                cv2.circle(fr, tuple(obj['verts'][i]), 4, (255, 100, 100), 1)
        if setts['dispCenters']:
            cv2.circle(fr, (obj['center']), 2, (50, 255, 50), 1)

    def detect_shapes(self, frame):
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

        # #####################################################################
        # FIND COUNTOURS
        # #####################################################################
        cnts = cv2.findContours(frame.copy(),
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        # #####################################################################
        # ANALYZE CONTOURS
        # #####################################################################

        # clear list
        self.objs = []

        for c in cnts:
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
            approx_cnt_X = int((M['m10'] / M['m00']))
            approx_cnt_Y = int((M['m01'] / M['m00']))

            obj = {'shape': shape,
                   'verts': verts,
                   'approx_cnt': approx_cnt,
                   'approx_cnt_area': approx_cnt_area,
                   'contour': c,
                   'center': (approx_cnt_X, approx_cnt_Y)}

            self.objs.append(obj)

            c = c.astype('float')
            c = c.astype('int')

            self.draw_cntrs_features(frame, self.settings, self.objs[j])


if __name__ == "__main__":
    vs = VisionSystem()
    vs.start()
