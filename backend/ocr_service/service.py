import json
import numpy as np
import math
import flask
from flask_cors import CORS
import datetime
import cv2
from config import input_size, charset_base, max_text_length, MODEL_PATH
from transcriptor import Transcriptor

app = flask.Flask(__name__)
CORS(app, support_credentials=True)

transcriptor = Transcriptor(model_path=MODEL_PATH,
                            input_image_size=input_size,
                            max_text_length=max_text_length,
                            charset=charset_base)


@app.route("/ocr", methods=["POST"])
def ocr():
    """
    This method exposes the service API to perform OCR on the lines of page image.
    The API can be called by sending an HTTP POST request to the /ocr path of the exposed server address.
    The following fields should be presentin the HTTP POST request:
        - a 'file' field with the file containing the image of the page to perform OCR on
        - a 'boxes' image with the list of coordinates for the bounding boxes of all the lines on the page
    """
    start_time = datetime.datetime.now()

    # the received HTTP POST request is accessible as flask.request

    # TODO: move the preprocessing of the read files to separate private methods
    # TODO: add checks for file types and sizes

    # extract the file and boxes from the HTTP POST request
    uploaded_file = flask.request.files.get('file')     # extract the image file from the HTTP POST
    boxes = flask.request.form.get('boxes')             # extract the bounding box coordinates from the HTTP POST
    boxes = json.loads(boxes)                           # deserialize the str of the bounding boxes to a JSON object

    # read the file of the uploaded image as a grayscale OpenCV image
    filestr = uploaded_file.read()
    numpy_image = np.frombuffer(filestr, np.uint8)
    page_image = cv2.imdecode(numpy_image, cv2.IMREAD_GRAYSCALE)

    # clean the coordinates of all the bounding boxes
    clean_boxes = []
    for current_box in boxes:
        cur_box_x, cur_box_y, cur_box_w, cur_box_h = math.ceil(current_box['x']), \
                                                     math.ceil(current_box['y']), \
                                                     math.ceil(current_box['width']), \
                                                     math.ceil(current_box['height'])
        clean_boxes.append((cur_box_x, cur_box_y, cur_box_w, cur_box_h))

    transcriptions, probabilities = transcriptor.transcribe(page_image, clean_boxes)
    end_time = datetime.datetime.now()
    print('Transcription time:', end_time - start_time)

    return flask.jsonify({'predictions': transcriptions,
                          'probabilities': probabilities}), 200


'''
@app.route('/ocr-polygon',methods=['POST'])
def ocr_polygon():
    print('read image')
    uploaded_file = flask.request.files.get('file')
    boxes = flask.request.form.get('boxes')
    boxes = json.loads(boxes)
    boxes = [b['bounding_box'] for b in boxes]
    npimg = np.frombuffer(uploaded_file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)

    print(img)

    short_size = 1024
    resized_image = resize_image_from_short_side(img, short_size)

    old_height, old_width = img.shape
    height, width = resized_image.shape
    width_aspect_ratio = float(width) / float(old_width)
    height_aspect_ratio = float(height) / float(old_height)

    diagonal = int(np.sqrt(height ** 2 + width ** 2))
    center_x, center_y = diagonal // 2, diagonal // 2

    base_img = np.zeros([diagonal, diagonal])
    base_height, base_width = base_img.shape
    base_img[center_y - height // 2: center_y + height // 2, center_x - width // 2: center_x + width // 2] = resized_image
    diff_w, diff_h = (base_width - width) // 2, (base_height - height) // 2

    input_size = (640, 64, 1)
    images_roi = []

    for points in boxes:
        points_list = [math.ceil(p) for p in points]
        pts = list(zip(points_list[::2], points_list[1::2]))
        pts = [[x, y] for (x, y) in pts]
        pts = rescale_points(pts, width_aspect_ratio, height_aspect_ratio)
        translated_pts = []
        for p in pts:
            translated_pts.append([p[0] + diff_w, p[1] + diff_h])
        translated_pts = np.array(translated_pts, dtype=np.int32)
        rect = cv2.minAreaRect(translated_pts)
        roi = get_sub_image(rect, base_img)
        images_roi.append(preprocess(roi, input_size, predict=True))

    lines = images_roi
    print('n box:', len(lines))

    batch_size = 64
    dtgen.batch_size = batch_size

    print('start_predict')
    predicts_list = []
    probabilities_list = []

    for i in range(len(lines) // batch_size):
        predicts, probabilities = model.predict(normalize(lines[i * batch_size:(i + 1) * batch_size]),
                                                dtgen,
                                                ctc_decode=True,
                                                verbose=1,
                                                )
        predicts_list.extend(predicts)
        probabilities_list.extend(probabilities)

    if len(predicts_list) != len(lines):
        predicts, probabilities = model.predict(normalize(lines[len(predicts_list):]),
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
'''


app.run(debug=True, port=5025)
print('ocr server is running...')

