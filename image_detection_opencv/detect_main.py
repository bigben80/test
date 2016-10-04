# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2

haarcascade_path = '/usr/share/opencv/haarcascades/'

def detect_face(frame, gray):

    face_cascade_path = haarcascade_path + 'haarcascade_frontalface_default.xml'
    eye_cascade_path = haarcascade_path + 'haarcascade_eye.xml'

    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    face_count = 0
    eyes_count = 0

    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        face_count += 1
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
            eyes_count += 1

    return face_count, eyes_count, frame


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




 
def loop_frames(camera, min_area):
 
    # initialize the first frame in the video stream
    firstFrame = None
    
    # loop over the frames of the video
    while True:
        # grab the current frame and initialize the occupied/unoccupied
        # text
        (grabbed, frame) = camera.read()
        #text = "Unoccupied"
 
        # if the frame could not be grabbed, then we have reached the end
        # of the video
        if not grabbed:
            break
 
        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_gauss = cv2.GaussianBlur(gray, (21, 21), 0)
 
        # if the first frame is None, initialize it
        if firstFrame is None:
            firstFrame = gray_gauss
            continue

        # detect if there's any motion in the video, comparing with first frame
        motion_detected = False

        (motion_detected, frame, delta_frame) = detect_motion(firstFrame, gray_gauss, frame, min_area)
        
        if motion_detected > 0:
            print "{} object or person moving in video!!!".format(motion_detected)

            # detect faces
            (face_count, eyes_count, frame) = detect_face(frame, gray)
            #(face_count, eyes_count, frame) = detect_face(frame, delta_frame)
            print'{} faces and {} eyes detected'.format(face_count,eyes_count)
           
           

        #frame = detect_upper_body(frame, gray)

        # draw the text and timestamp on the frame
        #cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
        #    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
 
        # show the frame and record if the user presses a key
        cv2.imshow("Security Feed", frame)
        #cv2.imshow("Thresh", thresh)
        #cv2.imshow("Frame Delta", frameDelta)
        key = cv2.waitKey(1) & 0xFF
 
        # if the `q` key is pressed, break from the lop
        if key == ord("q"):
            break
 

def main(input_filename, min_area):
    print "Starting..."


    # if the video argument is None, then we are reading from webcam
    if input_filename == "camera":
        camera = cv2.VideoCapture(0)
        time.sleep(0.25)
 
    # otherwise, we are reading from a video file
    else:
        camera = cv2.VideoCapture(input_filename)
 
    # loop video frames
    loop_frames(camera, int(min_area))

    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()


#    with open(input_filename, 'rb') as image:
#        print "Processing file: ", input_filename
#        faces = detect_face(image, max_results)
#        print('Found %s face%s' % (len(faces), '' if len(faces) == 1 else 's'))
#
#        print('Writing to file %s' % output_filename)
#        # Reset the file pointer, so we can read the file again
#        image.seek(0)
#        highlight_faces(image, faces, output_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detects motion from video or camer')
    parser.add_argument(
        'input_filename',
        help='the device you want to detect motion. video file name or camera')
    parser.add_argument(
        'min_area',
        help='the minimal area size of motion area, smaller motion will be ignored.')
    args = parser.parse_args()

    main(args.input_filename, args.min_area)

