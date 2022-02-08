from flask import Flask, request, jsonify
from flask_cors import CORS
from text_detection import text_detection
from model import DBNet
from config import MODEL_PATH, DBConfig

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

@app.route('/mybiros/api/v1/text-detection/corpus/', methods=['POST'])
def segmentation_corpus():

    if request.method == 'POST':
        corpus = request.files.to_dict()    # convert in mutable dict, useful but not necessary
        print(corpus)
        corpus_segmentation = []
        for file in corpus.keys():
            bb = text_detection(corpus[file], text_detector)
            corpus_segmentation.append({file: bb})    # batch
        return jsonify({'segmentation': corpus_segmentation}), 200
    else:
        return "sorry, bad request", 400


# init text detector
cfg = DBConfig()
text_detector = init_text_detector(MODEL_PATH)

# run flask app
print('text detector server is running...')
app.run(debug=True, port=5015)

