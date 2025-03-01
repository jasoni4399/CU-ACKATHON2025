import numpy as np
import cv2
from flask import Flask, render_template, request, Response, jsonify
from googletrans import Translator
from transformers import pipeline, AutoImageProcessor, AutoModelForImageClassification

# Use a pipeline as a high-level helper
pipe = pipeline("image-classification", model="Hemg/sign-language-classification")

processor = AutoImageProcessor.from_pretrained("Hemg/sign-language-classification")
model = AutoModelForImageClassification.from_pretrained("Hemg/sign-language-classification")

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        

    def __del__(self):
        self.video.release()        

    def get_frame(self):
        ret, frame = self.video.read()
        while frame is None:
            self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            ret, frame = self.video.read()

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), frame

app = Flask(__name__)

video_stream = VideoCamera()
#close the cam when the app is closed
@app.teardown_appcontext    
def close_camera(exception):
    video_stream.__del__()

def gen(camera):    
    while True:
        frame, _ = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

#sign language classification
@app.route('/classify', methods=['POST'])
def classify():
    _, frame = video_stream.get_frame()
    image = processor(images=frame, return_tensors="pt")
    outputs = model(**image)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    predicted_class = pipe.model.config.id2label[predicted_class_idx]
    return jsonify({'predictedClass': predicted_class})

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