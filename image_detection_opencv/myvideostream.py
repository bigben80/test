# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from picamera import PiCameraCircularIO
from threading import Thread
import cv2
import io
import datetime

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
                self.gray = None
                self.gauss_gray = None
                self.frame_consistent = None
		self.stopped = False
                self.get_frame_no = 0
                self.get_frame_gray = 0
                self.get_frame_gauss = 0
                self.last_100_time = datetime.datetime.now()
                self.last_100_gray = self.last_100_time
                self.last_100_gauss = self.last_100_time
                self.http_frame_no = 0

                self.frame_grayed = False
                self.frame_gaussed = False
                self.alarm_enabled = False

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()

                t2 = Thread(target=self.update_consistent, args=())
                t2.daemon = True
                t2.start()

                t3 = Thread(target=self.to_gauss, args=())
                t3.daemon = True
                t3.start()


		return self

        def to_gray(self):
                while not self.stopped:
                    if (self.frame is not None):

                        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                        self.gray = gray
                        #self.frame_grayed = True

                        self.get_frame_gray += 1
                        if self.get_frame_gray >= 100:
                            print "convert 100 frames to gray in {} seconds".format( (datetime.datetime.now() - self.last_100_gray).seconds )
                            self.get_frame_gray = 0
                            self.last_100_gray = datetime.datetime.now()

        def to_gauss(self):
                while not self.stopped:
                    if (self.gray is not None):
                        gauss_gray = cv2.GaussianBlur(self.gray, (21, 21), 0)
                        self.gauss_gray = gauss_gray
                        #self.frame_gaussed = True
       
                        self.get_frame_gauss += 1
                        if self.get_frame_gauss >= 100:
                            print "convert 100 frames to gauss in {} seconds".format( (datetime.datetime.now() - self.last_100_gauss).seconds )
                            self.get_frame_gauss = 0
                            self.last_100_gauss = datetime.datetime.now()

	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
                        #gray = cv2.cvtColor(f.array, cv2.COLOR_BGR2GRAY)
                        #gray = cv2.GaussianBlur(gray, (21, 21), 0)
                        #self.frame = gray
                        self.frame = f.array

                        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                        self.gray = gray

                        #ret, jpg_frame = cv2.imencode('.jpg', self.frame)
                        #self.frame_consistent = jpg_frame.tostring()

			self.rawCapture.truncate(0)

                        #self.frame_grayed = False
                        #self.frame_gaussed = False

                        self.get_frame_no += 1
                        if self.get_frame_no >= 100:
                            print "captured 100 frames in {} seconds".format( (datetime.datetime.now() - self.last_100_time).seconds )
                            self.get_frame_no = 0
                            self.last_100_time = datetime.datetime.now()

			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return

        def update_consistent(self):
                while not self.stopped:
                    if self.frame is not None:

                        ts = datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")

                        frame = self.frame

                        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 0, 255), 1)                        

                        cv2.putText(frame, "Alarm Status: {}".format(self.alarm_enabled), (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)

                        ret, jpg_frame = cv2.imencode('.jpg', frame)
                        self.frame_consistent = jpg_frame.tostring()

                        if self.stopped:
                                self.camera.capture_continuous.close()
                                self.camera.close()
                                return

	def read(self):
		# return the frame most recently read
		#return self.frame
                return self.gauss_gray
        def read_consistent(self):
                # return the frame most recently read
                return self.frame_consistent
                return 

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
