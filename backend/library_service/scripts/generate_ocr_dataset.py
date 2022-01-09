import glob
import os
import json
from shutil import copyfile

RUN_FOLDER = './'

DATASET_ROOT_PATH = os.path.join(RUN_FOLDER, 'ocr_dataset')
TRAIN_PATH = os.path.join(DATASET_ROOT_PATH, 'train')
TEST_PATH = os.path.join(DATASET_ROOT_PATH, 'test')

if not os.path.isdir(DATASET_ROOT_PATH):
    os.makedirs(DATASET_ROOT_PATH)
    os.mkdir(TRAIN_PATH)
    os.mkdir(TEST_PATH)

split_source = 'split.json'
INPUT_FOLDER_IMAGES = os.path.join(RUN_FOLDER,'clips')


with open(split_source, 'r') as gt_split:
    gt_split_json = json.load(gt_split)
    valid_list = gt_split_json['test_list']

    images = os.listdir(INPUT_FOLDER_IMAGES)

    for dir in images:


        clip_ocr = glob.glob(os.path.join(INPUT_FOLDER_IMAGES, dir, '*.jpg'))
        gt_ocr = glob.glob(os.path.join(INPUT_FOLDER_IMAGES, dir, '*.txt'))
        valid_list = [v.replace('.jpg','') for v in valid_list]
        if dir in valid_list:
            for clip, gt in zip(clip_ocr, gt_ocr):
                filename_clip = clip.split(os.sep)[-1]
                filename_gt = gt.split(os.sep)[-1]
                copyfile(clip, os.path.join(TEST_PATH, filename_clip))
                copyfile(gt, os.path.join(TEST_PATH, filename_gt))
        else:
            for clip, gt in zip(clip_ocr, gt_ocr):
                filename_clip = clip.split(os.sep)[-1]
                filename_gt = gt.split(os.sep)[-1]
                copyfile(clip, os.path.join(TRAIN_PATH, filename_clip))
                copyfile(gt, os.path.join(TRAIN_PATH, filename_gt))