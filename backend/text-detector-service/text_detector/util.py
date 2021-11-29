# -*- coding: utf-8 -*-
# @Time    : 2020/6/16 23:51
# @Author  : zonas.wang
# @Email   : zonas.wang@gmail.com
# @File    : inference.py
import math
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import os.path as osp
import time

import tensorflow as tf
import cv2
import glob
import numpy as np
import pyclipper
from shapely.geometry import Polygon
from tqdm import tqdm

from model import DBNet
from config import DBConfig

cfg = DBConfig()

import string
from data.generator import DataGenerator
from data.preproc import normalization, preprocess
from network.model import HTRModel
from functools import cmp_to_key


def resize_image(image, image_short_side=736):
    height, width, _ = image.shape
    if height < width:
        new_height = image_short_side
        new_width = int(math.ceil(new_height / height * width / 32) * 32)
    else:
        new_width = image_short_side
        new_height = int(math.ceil(new_width / width * height / 32) * 32)
    resized_img = cv2.resize(image, (new_width, new_height))
    return resized_img


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


def getSubImage(rect, src):
    # print('rect' , rect)
    # Get center, size, and angle from rect
    center, size, theta = rect
    # print('angle:' , theta)
    # Convert to int
    center, size = tuple(map(int, center)), tuple(map(int, size))
    # Get rotation matrix for rectangle
    M = cv2.getRotationMatrix2D(center, theta, 1)
    # Perform rotation on src image
    dst = cv2.warpAffine(src, M, src.shape[:2])
    cv2.imwrite('dst.jpg', dst)

    # cv2.imwrite('dst.jpg', dst)
    dst = np.float32(dst)
    out = cv2.getRectSubPix(dst, size, center)
    cv2.imwrite('out.jpg', out)

    h_out, w_out, _ = out.shape

    if w_out < h_out:
        out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
    # imwrite('dst.jpg' , dst)
    return out


def load_model(arch, input_size, dtgen, weights_path):
    model = HTRModel(architecture=arch,
                     input_size=input_size,
                     vocab_size=dtgen.tokenizer.vocab_size,
                     beam_width=0,
                     greedy=True)
    model.load_checkpoint(target=weights_path)
    return model


def x_y_compare(p0, p1):
    # print(p0, p1)
    x0, y0 = p0[0][0], p0[0][1]
    x1, y1 = p1[0][0], p1[0][1]

    if abs(y0 - y1) <= 15:
        if x0 > x1:
            return 1
        elif x0 < x1:
            return -1
        else:
            return 0

    elif y0 > y1:
        return 1
    elif y0 < y1:
        return -1
    else:
        return 0


def text_detection(img):

    BOX_THRESH = 0.5
    mean = np.array([103.939, 116.779, 123.68])

    # model_path = "db_weights.h5"

    # img_dir = 'datasets/data/test_v'
    # img_names = os.listdir(img_dir)

    # arch = 'flor'
    # input_size = (1024, 128, 1)
    # charset_base = string.printable[:95] + '€'
    # max_text_length = 128
    print('init generator')
    # dtgen = DataGenerator(None, None, charset_base, max_text_length, predict=True, lines=None)
    print('init model')
    # ocr_model = load_model(arch, input_size, dtgen,'checkpoint_weights_2.52.hdf5')

    # model = DBNet(cfg, model='inference')
    # model.load_weights(model_path, by_name=True, skip_mismatch=True)

    # ocr_model = load_model(arch, input_size, dtgen, 'checkpoint_weights_2.52.hdf5')

    # for img_name in img_names:
    # img_path = osp.join(img_dir, img_name)
    image = cv2.imread(img_path)
    src_image = image.copy()
    cv2.imwrite('src.jpg', src_image)
    h, w = image.shape[:2]
    image_base = resize_image(image)
    image = image_base.astype(np.float32)
    image -= mean
    image_input = np.expand_dims(image, axis=0)
    image_input_tensor = tf.convert_to_tensor(image_input)
    start_time = time.time()
    p = model.predict(image_input_tensor)[0]
    end_time = time.time()
    print("time: ", end_time - start_time)

    # ----------------
    h, w, _ = src_image.shape
    diagonal = int(np.sqrt(h ** 2 + w ** 2))
    center_x, center_y = diagonal // 2, diagonal // 2
    base_img = np.zeros([diagonal, diagonal, 3])
    base_h, base_w, _ = base_img.shape
    base_img[int(center_y - h / 2): int(center_y + h / 2), int(center_x - w / 2): int(center_x + w / 2)] = src_image

    diff_w, diff_h = (base_w - w) // 2, (base_h - h) // 2

    #images_roi = []

    bitmap = p > 0.3
    boxes, scores = polygons_from_bitmap(p, bitmap, w, h, box_thresh=BOX_THRESH)
    x_y_compare_func = cmp_to_key(x_y_compare)
    boxes = sorted(boxes, key=x_y_compare_func)

    bounding_box = []

    for i, box in enumerate(boxes):
        # print(box)
        points = [item for sublist in box for item in sublist]
        points_list = [math.ceil(p) for p in points]
        pts = list(zip(points_list[::2], points_list[1::2]))
        pts = [[x, y] for (x, y) in pts]
        pts = np.array(pts, dtype=np.int32)
        translated_pts = []
        for p in pts:
            translated_pts.append([p[0] + diff_w, p[1] + diff_h])
        translated_pts = np.array(translated_pts, dtype=np.int32)
        bounding_box.append(translated_pts)

    return bounding_box



if __name__ == '__main__':
    main()
