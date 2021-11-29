from flask import Flask, request
from flask_cors import CORS
from db_segmentation import text_detection
from text_detector.model import DBNet
from text_detector.config import DBConfig
from config import MODEL_PATH

# init flask app
app = Flask(__name__)
CORS(app)


def init_text_detector(model_path):
    print("Create TF DBNet")
    model = DBNet(cfg, model='inference')
    model.load_weights(model_path, by_name=True, skip_mismatch=True)
    return model

@app.route('/')
def hello():
    return 'Hello :-)'

@app.route('/mybiros/api/v1/text-detection/image/', methods=['POST'])
def segmentation():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        bb = text_detection(uploaded_file, text_detector)
        print(bb)
        return bb, 200
    else:
        return "sorry, bad request", 400



# init text detector
cfg = DBConfig()
text_detector = init_text_detector(MODEL_PATH)

# run flask app
print('text detector server is running...')
app.run(debug=True, port=5015)

