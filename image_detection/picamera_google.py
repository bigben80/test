#!/usr/bin/env python

import picamera
import datetime
import io




camera = picamera.PiCamera()
camera.rotation = 180
camera.framerate = 32
camera.resolution = [640, 480]
stream = io.BytesIO()

frame_count = 0

while True:
    camera.capture_sequence([
          'image1.jpg',
          'image2.jpg',
          'image3.jpg',
          'image4.jpg',
          'image5.jpg',
          'image6.jpg',
          'image7.jpg',
          'image8.jpg',
          'image9.jpg',
          'image10.jpg',
        ])
    frame_count += 10
    print frame_count

   
