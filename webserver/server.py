#!/usr/bin/env python
from flask import Flask, render_template, Response
from picamera import PiCamera
from myvideostream import MyPiVideoStream
import time

from OpenSSL import SSL

from gevent.pywsgi import WSGIServer

vs = MyPiVideoStream(rotation=180).start()
time.sleep(1)
 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen():
#    vs = MyPiVideoStream(rotation=180).start()
#    time.sleep(1)
    while True:
        frame = vs.read_consistent()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':

    http_server = WSGIServer(('0.0.0.0', 7737), app, keyfile='domain.key', certfile='domain.crt')
    http_server.serve_forever()


