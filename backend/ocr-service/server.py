import json
import numpy as np
import tensorflow as tf
import cv2
from data.generator import DataGenerator
from data.preproc import normalization, preprocess
from network.model import HTRModel
import math
import os
import flask
from flask_cors import CORS
import datetime
from numpy import frombuffer, uint8
from cv2 import IMREAD_GRAYSCALE, imdecode, IMREAD_COLOR
from config import arch, input_size, charset_base, max_text_length, model_path

#os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
app = flask.Flask(__name__)
CORS(app)

def update_point_with_aspect_ratio(point_list, w_ratio, h_ratio):
    #print('point_list', point_list)
    resized_points = []
    for point in point_list:
        resized_points.append([int(point[0] * w_ratio), int(point[1] * h_ratio)])
    resized_points = np.array(resized_points, dtype=np.int32)
    return resized_points


def load_model(arch, input_size, dtgen, weights_path):
    model = HTRModel(architecture=arch,
                     input_size=input_size,
                     vocab_size=dtgen.tokenizer.vocab_size,
                     beam_width=10,
                     greedy=True)
    model.load_checkpoint(target=weights_path)
    return model


def resize_image_greyscale(img, short_size):
    height, width = img.shape
    if height < width:
        new_height = short_size
        new_width = new_height / height * width
    else:
        new_width = short_size
        new_height = new_width / width * height
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)
    resized_img = cv2.resize(img, (new_width, new_height))
    return resized_img, new_width, new_height


def getSubImage(rect, src):
    print('rect', rect)
    # Get center, size, and angle from rect
    center, size, theta = rect
    print('angle:', theta)
    # Convert to int
    center, size = tuple(map(int, center)), tuple(map(int, size))
    # Get rotation matrix for rectangle
    M = cv2.getRotationMatrix2D(center, theta, 1)
    # Perform rotation on src image
    dst = cv2.warpAffine(src, M, src.shape[:2])
    # cv2.imwrite('dst.jpg', dst)
    dst = np.float32(dst)
    out = cv2.getRectSubPix(dst, size, center)

    h_out, w_out = out.shape

    if w_out < h_out:   # naive
        out = cv2.rotate(out, cv2.cv2.ROTATE_90_CLOCKWISE)

    return out

@app.route("/ocr", methods=["POST"])
def predict_HTR():
    start_time = datetime.datetime.now()

    print(flask.request)

    # get file and get boxes
    print('get file and boxes')
    uploaded_file = flask.request.files.get('file')
    boxes = flask.request.form.get('boxes')
    boxes = json.loads(boxes)

    # read file
    print('read image')
    filestr = uploaded_file.read()
    npimg = frombuffer(filestr, uint8)
    img = imdecode(npimg, IMREAD_GRAYSCALE)

    # crop lines
    print('crop lines')
    lines = []
    input_size = (640, 64, 1)
    for box in boxes:
        x = math.ceil(box['x'])
        y = math.ceil(box['y'])
        w = math.ceil(box['width'])
        h = math.ceil(box['height'])
        crop_img = img[y:y + h, x:x + w]
        lines.append(preprocess(crop_img, input_size, predict=True))
        # cv2.imwrite('test_img.png', preprocess(crop_img, input_size, predict=True))

    print('n lines:', len(lines))
    batch_size = 64

    dtgen.batch_size = batch_size

    print('start_predict')

    predicts_list = []
    probabilities_list = []

    for i in range(len(lines) // batch_size):
        predicts, probabilities = model.predict(normalization(lines[i * batch_size:(i + 1) * batch_size]),
                                                dtgen,
                                                ctc_decode=True,
                                                verbose=1,
                                                )
        predicts_list.extend(predicts)
        probabilities_list.extend(probabilities)

    if len(predicts_list) != len(lines):
        predicts, probabilities = model.predict(normalization(lines[len(predicts_list):]),
                                                dtgen,
                                                steps=1,
                                                ctc_decode=True,
                                                verbose=1,
                                                )
        predicts_list.extend(predicts)
        probabilities_list.extend(probabilities)

    predicts_list = tf.sparse.to_dense(predicts_list[0]).numpy()
    probabilities_list = [prob.numpy() for prob in probabilities_list]
    probabilities_list = [str(np.exp(prob[0])) for prob in probabilities_list]
    # decode to string
    predicts_list = [dtgen.tokenizer.decode(x) for x in predicts_list]

    print('end predict')
    end_time = datetime.datetime.now()
    print('total time:', end_time - start_time)

    print(predicts_list, probabilities_list)

    return flask.jsonify({'predictions': predicts_list, 'probabilities': probabilities_list}), 200

@app.route('/ocr-polygon',methods=['POST'])
def predict():
    print('read image')
    uploaded_file = flask.request.files.get('file')
    boxes = flask.request.form.get('boxes')
    boxes = json.loads(boxes)
    boxes = [b['bounding_box'] for b in boxes]
    npimg = np.frombuffer(uploaded_file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)

    short_size = 1024
    resized_image, resized_w, resized_h = resize_image_greyscale(img, short_size)
    height, width = img.shape
    aspect_ratio_w = resized_w / width
    aspect_ratio_h = resized_h / height
    h, w = resized_image.shape
    diagonal = int(np.sqrt(h ** 2 + w ** 2))
    center_x, center_y = diagonal // 2, diagonal // 2
    base_img = np.zeros([diagonal, diagonal])
    base_h, base_w = base_img.shape
    base_img[center_y - h // 2: center_y + h // 2, center_x - w // 2: center_x + w // 2] = resized_image
    diff_w, diff_h = (base_w - w) // 2, (base_h - h) // 2

    input_size = (640, 64, 1)
    images_roi = []

    for points in boxes:
        #print('points', points)
        points_list = [math.ceil(p) for p in points]
        pts = list(zip(points_list[::2], points_list[1::2]))
        pts = [[x, y] for (x, y) in pts]
        pts = np.array(pts, dtype=np.int32)
        pts = update_point_with_aspect_ratio(pts, aspect_ratio_w, aspect_ratio_h)
        translated_pts = []
        for p in pts:
            translated_pts.append([p[0] + diff_w, p[1] + diff_h])
        translated_pts = np.array(translated_pts, dtype=np.int32)
        rect = cv2.minAreaRect(translated_pts)
        roi = getSubImage(rect, base_img)
        images_roi.append(preprocess(roi, input_size, predict=True))

    lines = images_roi
    print('n box:', len(lines))

    batch_size = 64
    dtgen.batch_size = batch_size

    print('start_predict')
    predicts_list = []
    probabilities_list = []

    for i in range(len(lines) // batch_size):
        predicts, probabilities = model.predict(normalization(lines[i * batch_size:(i + 1) * batch_size]),
                                                dtgen,
                                                ctc_decode=True,
                                                verbose=1,
                                                )
        predicts_list.extend(predicts)
        probabilities_list.extend(probabilities)

    if len(predicts_list) != len(lines):
        predicts, probabilities = model.predict(normalization(lines[len(predicts_list):]),
                                                dtgen,
                                                steps=1,
                                                ctc_decode=True,
                                                verbose=1,
                                                )
        predicts_list.extend(predicts)
        probabilities_list.extend(probabilities)

    predicts_list = tf.sparse.to_dense(predicts_list[0]).numpy()
    probabilities_list = [prob.numpy() for prob in probabilities_list]
    probabilities_list = [str(np.exp(prob[0])) for prob in probabilities_list]

    # decode to string
    predicts_list = [dtgen.tokenizer.decode(x) for x in predicts_list]
    print('end predict')

    print(predicts_list, probabilities_list)

    return flask.jsonify({'predictions': predicts_list, 'probabilities': probabilities_list}), 200


def load_model(arch, input_size, dtgen, model_path):

    model = HTRModel(architecture=arch,
                     input_size=input_size,
                     vocab_size=dtgen.tokenizer.vocab_size,
                     beam_width=0,
                     greedy=True)

    print('load model with ' + model_path, 'weights')
    model.load_checkpoint(target=model_path)
    return model

print('ocr server is running...')
dtgen = DataGenerator(None, None, charset_base, max_text_length, predict=True, lines=None)
model = load_model(arch, input_size, dtgen, model_path)
app.run(debug=True, host='0.0.0.0', port="5025")
