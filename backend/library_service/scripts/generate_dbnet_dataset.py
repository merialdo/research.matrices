import os
import json
from shutil import copyfile


RUN_FOLDER = './'

RAW_DATASET = os.path.join(RUN_FOLDER, 'dataset.json')
INPUT_IMAGES = os.path.join(RUN_FOLDER, 'raw_images')

DATASET_ROOT_PATH = os.path.join(RUN_FOLDER, 'text_detector_dataset/data')
TRAIN_PATH = os.path.join(RUN_FOLDER, 'text_detector_dataset/data/train')
VAL_PATH = os.path.join(RUN_FOLDER, 'text_detector_dataset/data/val')

if not os.path.isdir(DATASET_ROOT_PATH):
    os.makedirs(DATASET_ROOT_PATH)
    os.mkdir(TRAIN_PATH)
    os.mkdir(VAL_PATH)

split_source = 'split.json'

val_dict = dict()
val_dict['data_root'] = 'text_detector_dataset/data/val'
val_dict['data_list'] = []

train_dict = dict()
train_dict['data_root'] = 'text_detector_dataset/data/train'
train_dict['data_list'] = []

with open(split_source, 'r') as gt_split, open(RAW_DATASET, 'r') as raw_dataset:
    gt_split_json = json.load(gt_split)
    valid_list = gt_split_json['test_list']

    raw_dataset_json = json.load(raw_dataset)
    raw_data_list = raw_dataset_json['data_list']

    for elem in raw_data_list:
        filename = elem['img_name']
        img = os.path.join(INPUT_IMAGES, filename)

        if elem['annotations']:

            if filename in valid_list:
                print(filename)
                copyfile(img, os.path.join(VAL_PATH, filename))
                val_dict['data_list'].append(elem)
            else:
                copyfile(img, os.path.join(TRAIN_PATH, filename))
                train_dict['data_list'].append(elem)

    with open(os.path.join(DATASET_ROOT_PATH, 'val.json'), 'w') as valid_json, \
            open(os.path.join(DATASET_ROOT_PATH, 'train.json'), 'w') as train_json:
        json.dump(val_dict, valid_json)
        json.dump(train_dict, train_json)
