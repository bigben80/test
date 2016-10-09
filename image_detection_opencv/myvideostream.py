# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from picamera import PiCameraCircularIO
from threading import Thread
import cv2
import io

class MyPiVideoStream:
	def __init__(self, resolution=(320, 240), rotation=0,framerate=32):
		# initialize the camera and stream
		self.camera = PiCamera()
                self.camera.rotation = rotation
		self.camera.resolution = resolution
		self.camera.framerate = framerate
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)

                self.stream_consistent = io.BytesIO()
		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
                self.frame_consistent = None
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()

                t2 = Thread(target=self.update_consistent, args=())
                t2.daemon = True
                t2.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.stream:
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

        def update_consistent(self):
                # keep looping infinitely until the thread is stopped
                for f in self.camera.capture_continuous(self.stream_consistent, 'jpeg', use_video_port=False):
                #for f in self.camera.capture_continuous('img{counter:02d}.jpg'):
                        # grab the frame from the stream and clear the stream in
                        # preparation for the next frame
                        self.stream_consistent.seek(0)
                        #self.frame_consistent = Image.open(self.stream_consistent)
                        self.frame_consistent = self.stream_consistent.read()

                        self.stream_consistent.seek(0)
                        self.stream_consistent.truncate() 

                        # if the thread indicator variable is set, stop the thread
                        # and resource camera resources
                        if self.stopped:
                                self.camera.capture_continuous.close()
                                self.camera.close()
                                return

	def read(self):
		# return the frame most recently read
		return self.frame
        def read_consistent(self):
                # return the frame most recently read
                return self.frame_consistent

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
