#!python2
# -*- coding: UTF-8 -*-


# import the necessary packages
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import signal
# import cv2


class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=30):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

        self.t = Thread(target=self.update, args=())

        self.startTime = 0
        self.endTime = 0
        self.dt = 0

    def start(self):
        # start the thread to read frames from the video stream
        self.t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            self.startTime = time.time()
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

            self.endTime = time.time()
            self.dt = self.endTime - self.startTime

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
        self.t.join()


if __name__ == "__main__":
    try:
        pvs = PiVideoStream()
        pvs.start()
        # pauses main thread in this place so it can catch
        # exceptions; otherwise try/except just ends and thread
        # is running in the background
        signal.pause()
    except KeyboardInterrupt:
        pvs.stop()
        print('Keyboard Interrupt')
    except Exception as e:
        pvs.stop()
        print(e)
