import cv2
import numpy as np
import datetime
import tensorflow as tf
from shapely.geometry import Polygon
import pyclipper

# Mettere tutto in una classe

def box_score_fast(bitmap, _box):
    h, w = bitmap.shape[:2]
    box = _box.copy()
    xmin = np.clip(np.floor(box[:, 0].min()).astype(np.int), 0, w - 1)
    xmax = np.clip(np.ceil(box[:, 0].max()).astype(np.int), 0, w - 1)
    ymin = np.clip(np.floor(box[:, 1].min()).astype(np.int), 0, h - 1)
    ymax = np.clip(np.ceil(box[:, 1].max()).astype(np.int), 0, h - 1)

    mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
    box[:, 0] = box[:, 0] - xmin
    box[:, 1] = box[:, 1] - ymin
    cv2.fillPoly(mask, box.reshape(1, -1, 2).astype(np.int32), 1)
    return cv2.mean(bitmap[ymin:ymax + 1, xmin:xmax + 1], mask)[0]


def unclip(box, unclip_ratio=1.5):
    poly = Polygon(box)
    distance = poly.area * unclip_ratio / poly.length
    offset = pyclipper.PyclipperOffset()
    offset.AddPath(box, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    expanded = np.array(offset.Execute(distance))
    return expanded


def get_mini_boxes(contour):
    if not contour.size:
        return [], 0
    bounding_box = cv2.minAreaRect(contour)
    points = sorted(list(cv2.boxPoints(bounding_box)), key=lambda x: x[0])

    index_1, index_2, index_3, index_4 = 0, 1, 2, 3
    if points[1][1] > points[0][1]:
        index_1 = 0
        index_4 = 1
    else:
        index_1 = 1
        index_4 = 0
    if points[3][1] > points[2][1]:
        index_2 = 2
        index_3 = 3
    else:
        index_2 = 3
        index_3 = 2

    box = [points[index_1], points[index_2],
           points[index_3], points[index_4]]
    return box, min(bounding_box[1])


def polygons_from_bitmap(pred, bitmap, dest_width, dest_height, max_candidates=500, box_thresh=0.7):
    pred = pred[..., 0]
    bitmap = bitmap[..., 0]
    height, width = bitmap.shape
    boxes = []
    scores = []

    contours, _ = cv2.findContours((bitmap * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours[:max_candidates]:
        epsilon = 0.001 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        points = approx.reshape((-1, 2))
        if points.shape[0] < 4:
            continue
        score = box_score_fast(pred, points.reshape(-1, 2))
        if box_thresh > score:
            continue
        if points.shape[0] > 2:
            box = unclip(points, unclip_ratio=2.0)
            if len(box) > 1:
                continue
        else:
            continue

        box = box.reshape(-1, 2)
        _, sside = get_mini_boxes(box.reshape((-1, 1, 2)))
        if sside < 5:
            continue

        box[:, 0] = np.clip(np.round(box[:, 0] / width * dest_width), 0, dest_width)
        box[:, 1] = np.clip(np.round(box[:, 1] / height * dest_height), 0, dest_height)
        boxes.append(box.tolist())
        scores.append(score)
    return boxes, scores


def resize_image_bigsize(img, big_size):
    height, width, _ = img.shape
    if height > width:
        new_height = big_size
        new_width = new_height / height * width
    else:
        new_width = big_size
        new_height = new_width / width * height
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)
    resized_img = cv2.resize(img, (new_width, new_height))
    return resized_img, new_width, new_height


def text_detection(uploaded_file, text_detector):
    print('db_segmentation function started')
    start_time = datetime.datetime.now()

    BOX_THRESH = 0.5
    # mean = np.array([103.939, 116.779, 123.68])
    mean = np.array([179.0, 183.0, 190.0])

    # read file
    print('read image')
    print(type(uploaded_file))
    filestr = uploaded_file.read()
    print('uploaded_file', uploaded_file)
    npimg = np.frombuffer(filestr, np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    orig_h, orig_w = image.shape[:2]
    image, resize_w, resize_h = resize_image_bigsize(image, 2500)
    aspect_ratio_w, aspect_ratio_h = orig_w / resize_w, orig_h / resize_h

    image = image.astype(np.float32)
    image -= mean
    image_input = np.expand_dims(image, axis=0)
    image_input_tensor = tf.convert_to_tensor(image_input)

    p = text_detector.predict(image_input_tensor)[0]

    bitmap = p > 0.3
    boxes, scores = polygons_from_bitmap(p, bitmap, resize_w, resize_h, box_thresh=BOX_THRESH)

    rects = []
    for b in boxes:
        rect = cv2.minAreaRect(np.array(b))
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        rects.append(box.tolist())

    bb = []
    for i, box in enumerate(rects):
        bb.append([])
        for point in box:
            bb[i].append([point[0]*aspect_ratio_w, point[1]*aspect_ratio_h])

    boxes_poly = []
    for points in bb:
        np_points = np.array(points, dtype=np.int)
        boxes_poly.append(np_points.tolist())

    boxes_poly_sorted = sorted(boxes_poly , key=lambda k: [k[0][1], k[0][0]])

    rects = []
    for id, points in enumerate(boxes_poly_sorted):
        np_points = np.array(points, dtype=np.int)
        x, y, w, h = cv2.boundingRect(np_points)
        rects.append({'id': id, 'x': x, 'y': y, 'width': w, 'height': h})


    return {'bounding_box': rects, 'width': orig_w, 'height': orig_h}
