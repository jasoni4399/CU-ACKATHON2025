import numpy as np
import cv2
from flask import Flask, render_template, request, Response
from pipeline import Pipeline

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()        

    def get_frame(self):
        ret, frame = self.video.read()
        while frame is None:
            self.video = cv2.VideoCapture(0)
            ret, frame = self.video.read()

        # DO WHAT YOU WANT WITH TENSORFLOW / KERAS AND OPENCV

        ret, jpeg = cv2.imencode('.jpg', frame)

        return jpeg.tobytes()
    


app = Flask(__name__)

pipeline = Pipeline()

video_stream = VideoCamera()
#close the cam when the app is closed
@app.teardown_appcontext    
def close_camera(exception):
    video_stream.__del__()
    cv2.destroyAllWindows()

def gen(camera):    
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
     return Response(gen(video_stream),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()