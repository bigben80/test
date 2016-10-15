#!/usr/bin/env python

# import the necessary packages
import argparse
import datetime
import imutils
import cv2

import json

from picamera.array import PiRGBArray
#from imutils.video.pivideostream import PiVideoStream
from picamera import PiCamera
import cv2

from flask import Flask, render_template, Response, redirect, url_for, request, session, abort
from flask_login import LoginManager, UserMixin, \
                                login_required, login_user, logout_user

from myvideostream import MyPiVideoStream
import time

from OpenSSL import SSL

from gevent.pywsgi import WSGIServer


from twilio.rest import TwilioRestClient

from threading import Thread

# To find these visit https://www.twilio.com/user/account
ACCOUNT_SID = "AC3a23436f2ab5f9a0615c50d136c9aad9"
AUTH_TOKEN = "d30b5a3d12b8b621a12edc0217dc5982"
FROM_SERVICE_NUMBER = "+46769447309"


#haarcascade_path = '/usr/share/opencv/haarcascades/'
haarcascade_path = './'


vs = MyPiVideoStream(resolution=(640, 480)).start()
time.sleep(2)

app = Flask(__name__)

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

username = json.load(open("config.json"))["username"]
password = json.load(open("config.json"))["password"]

class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = username
        self.password = password

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


users = [User(1)]

def detect_face(gray):

    face_cascade_path = haarcascade_path + 'haarcascade_frontalface_default.xml'
    eye_cascade_path = haarcascade_path + 'haarcascade_eye.xml'

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    face_count = 0
    eyes_count = 0

    for (x,y,w,h) in faces:
        face_count += 1
        roi_gray = gray[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex,ey,ew,eh) in eyes:
            eyes_count += 1

    print "Face {} detected!".format(face_count)
    return face_count, eyes_count


# detect the upper body in a frame.
#    "frame" should be the original frame
#    "gray" should be the  grayscaled original frame
#    return object is the frame with upper body marked
def detect_upper_body(frame, gray):
    # find upper body in the video frame
    #upperbody_cascade_path = haarcascade_path + 'haarcascade_upperbody.xml'
    upperbody_cascade_path = '/usr/share/opencv/haarcascades/haarcascade_upperbody.xml'

    upper_body_cascade = cv2.CascadeClassifier(upperbody_cascade_path)
    upper_body = upper_body_cascade.detectMultiScale(gray, 1.3, 5)

    body_cnt = 0
    for body in upper_body:
        body_cnt += 1
        print "find body %s", body_cnt
        # draw the border of detected upper body
        (x, y, w, h) = cv2.boundingRect(upper_body)
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

    return body_cnt, frame

def detect_motion(background, frame, original_frame, min_area):

    # compute the absolute difference between the current frame and
    # first frame
    frameDelta = cv2.absdiff(background, frame)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)

    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)


    find_motion = 0

    # loop over the contours
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < min_area:
            continue

        find_motion += 1
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return find_motion, original_frame, frameDelta



def trigger_alarm(message_body, target_mobile):

    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

    message = client.messages.create(
        body=message_body,  # Message body, if any
        to=target_mobile,
        from_=FROM_SERVICE_NUMBER,
    )

    print "alarm triggered"

def loop_frames_camera(conf, min_area):

    avg = None
    lastPeace = datetime.datetime.now()
    timestamp = lastPeace
    count_time = lastPeace
    lastMotion = lastPeace
    motionCounter = 0

    frame_no = 0
    brightness = 0

    #vs = PiVideoStream().start()
    time.sleep(3)

    # capture frames from the camera
    while True:

    	# grab the raw NumPy array representing the image and initialize
    	# the timestamp and occupied/unoccupied text
        #frame = vs.read()
        gray = vs.read()
    	timestamp = datetime.datetime.now()
    	text = "Unoccupied"

        frame_no += 1
        if frame_no >= 100:
            print "100 frames received in {} seconds".format((timestamp - count_time).seconds)
            count_time = timestamp
            frame_no = 0
    
    	# resize the frame, convert it to grayscale, and blur it
    	#frame = imutils.resize(frame, width=500)
    	#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    	#gray = cv2.GaussianBlur(gray, (21, 21), 0)
     
    	# if the average frame is None, initialize it
    	if avg is None:
    		print "[INFO] starting background model..."
    		avg = gray.copy().astype("float")
    		continue
     
    	# accumulate the weighted average between the current frame and
    	# previous frames, then compute the difference between the current
    	# frame and running average
    	cv2.accumulateWeighted(gray, avg, 0.5)
    	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    	
    	# threshold the delta image, dilate the thresholded image to fill
    	# in holes, then find contours on thresholded image
    	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
    		cv2.THRESH_BINARY)[1]
    	thresh = cv2.dilate(thresh, None, iterations=2)
    	(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    		cv2.CHAIN_APPROX_SIMPLE)
     
    	# loop over the contours
    	for c in cnts:
    		# if the contour is too small, ignore it
    		if cv2.contourArea(c) < conf["min_area"]:
    			continue
     
    		# compute the bounding box for the contour, draw it on the frame,
    		# and update the text
    		#(x, y, w, h) = cv2.boundingRect(c)
    		#cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    		text = "Occupied"
                lastMotion = timestamp
     

    	# check to see if the room is occupied
    	if text == "Occupied":
            # Measure motion amount and face detected in the last several seconds. if detected enough motion, or a lot faces detected, trigger alarm
            if (timestamp - lastPeace).seconds < conf["motion_detect_seconds"]:

                motionCounter += 1
                #print "current time: {}, Motion start from : {}, Motion detected: {}".format( timestamp, lastPeace, motionCounter)
                if (motionCounter >= conf["min_motion_frames"]):
                    print "continues motion detected! Motion frame number {}".format(motionCounter)

                    message_body = "Detect activitis in last {} seconds!".format(conf["motion_detect_seconds"])
                    target_mobile = conf["phone_number"]
                    trigger_alarm(message_body, target_mobile)

                    motionCounter = 0
                    lastPeace = timestamp
                else:
                    pass

            else:
                print "some motition detected but not continous. faulse detection? {} motion detected in {} seconds".format(motionCounter, conf["motion_detect_seconds"])
                motionCounter = 0
                lastPeace = timestamp

     
    	# otherwise, no motion detected in current frame, if no motion detected in last several seconds, clear motion status
    	elif (timestamp - lastMotion).seconds > 2.0:
    		motionCounter = 0
                lastPeace = timestamp
    	# check to see if the frames should be displayed to screen
    	if conf["show_video"]:
    		# display the security feed
    		cv2.imshow("Security Feed", frame)
    		key = cv2.waitKey(1) & 0xFF
     
    		# if the `q` key is pressed, break from the lop
    		if key == ord("q"):
    			break
     

app.route('/')
def index():
    return render_template('index.html')

def gen():
    while True:
        frame = vs.read_consistent()
        #frame = open("./seed.jpg")

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen(),
                mimetype='multipart/x-mixed-replace; boundary=frame')

# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        usernm = request.form['username']
        passwd = request.form['password']
        if passwd == password and usernm == username:
            id = 1
            user = User(id)
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)


def main(config_file):
    print "Starting..."


    conf = json.load(open(config_file))
    # if the video argument is None, then we are reading from webcam
    if conf["input_filename"] == "camera":
 
        #loop_frames_camera(conf, int(conf["min_area"]))

        t = Thread( target=loop_frames_camera, args=(conf, int(conf["min_area"])) )
        t.daemon = True
        t.start()

    # otherwise, we are reading from a video file
    else:
        camera = cv2.VideoCapture(input_filename)

        # loop video frames
        loop_frames(camera, int(min_area))
 

    http_server = WSGIServer(('0.0.0.0', 7737), app, keyfile='domain.key', certfile='domain.crt')
    http_server.serve_forever()


    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detects motion from video or camer')
    parser.add_argument(
        'config_file',
        help='the configuration json file')
    args = parser.parse_args()

    main(args.config_file)

