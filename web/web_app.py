import numpy as np
import cv2
from flask import Flask, render_template, request, Response, jsonify
from googletrans import Translator

# Use a pipeline as a high-level helper
from transformers import pipeline,AutoImageProcessor, AutoModelForImageClassification
pipe = pipeline("image-classification", model="Hemg/sign-language-classification")

processor = AutoImageProcessor.from_pretrained("Hemg/sign-language-classification")
model = AutoModelForImageClassification.from_pretrained("Hemg/sign-language-classification")

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

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

app = Flask(__name__)

video_stream = VideoCamera()
#close the cam when the app is closed
@app.teardown_appcontext    
def close_camera(exception):
    video_stream.__del__()

def gen(camera):    
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            
#sign language classification

translator = Translator()            
#translate the text to the desired language when save button is clicked
@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text')
    language = data.get('language')
    
    translated_text = translator.translate(text, dest=language).text
    return jsonify({'translatedText': translated_text})

@app.route('/video_feed')
def video_feed():
     return Response(gen(video_stream),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()