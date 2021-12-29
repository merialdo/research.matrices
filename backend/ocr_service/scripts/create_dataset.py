import argparse
import datetime
import html
import os
import re
import string
from pathlib import Path
import cv2
import h5py
import numpy
import sys

sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.dataset import Tokenizer
from backend.ocr_service.config import OCR_INPUT_IMAGE_SHAPE, OCR_MAX_TEXT_LENGTH, data_path
from backend.ocr_service.image_processing import preprocess

# define some important assets
alphabet = string.digits + string.ascii_letters + string.punctuation + '°' + 'àâéèêëîïôùûçÀÂÉÈËÎÏÔÙÛÇ' + '£€¥¢฿ '
input_image_size = OCR_INPUT_IMAGE_SHAPE
max_text_length = OCR_MAX_TEXT_LENGTH
tokenizer = Tokenizer(alphabet, max_text_length)

# DeepSpell based text cleaning process (Tal Weiss. Deep Spelling.)
#   As seen in Medium: https://machinelearnings.co/deep-spelling-9ffef96a24f6#.2c9pu8nlm
#   and Github: https://github.com/MajorTal/DeepSpell
RE_DASH_FILTER = re.compile(r'[\-\˗\֊\‐\‑\‒\–\—\⁻\₋\−\﹣\－]', re.UNICODE)
RE_APOSTROPHE_FILTER = re.compile(r'&#39;|[ʼ՚＇‘’‛❛❜ߴߵ`‵´ˊˋ{}{}{}{}{}{}{}{}{}]'.format(
    chr(768), chr(769), chr(832), chr(833), chr(2387),
    chr(5151), chr(5152), chr(65344), chr(8242)), re.UNICODE)
RE_RESERVED_CHAR_FILTER = re.compile(r'[¶¤«»]', re.UNICODE)
RE_LEFT_PARENTH_FILTER = re.compile(r'[\(\[\{\⁽\₍\❨\❪\﹙\（]', re.UNICODE)
RE_RIGHT_PARENTH_FILTER = re.compile(r'[\)\]\}\⁾\₎\❩\❫\﹚\）]', re.UNICODE)
RE_BASIC_CLEANER = re.compile(r'[^\w\s{}]'.format(re.escape(string.punctuation)), re.UNICODE)

LEFT_PUNCTUATION_FILTER = """!%&),.:;<=>?@\\]^_`|}~"""
RIGHT_PUNCTUATION_FILTER = """"(/<=>@[\\^_`{|~"""
NORMALIZE_WHITESPACE_REGEX = re.compile(r'[^\S\n]+', re.UNICODE)


def read_and_preprocess_transcription(transcription_path):
    with open(transcription_path, 'r', encoding='latin-1') as transcription_input:
        transcription = transcription_input.read().splitlines()[0].strip()
        transcription = transcription.replace("(", "").replace(")", "").replace("'", "")
        transcription = re.sub("\{.*?\}", "", transcription)
        transcription = re.sub("\[.*?\]", "", transcription)
        transcription = transcription.replace("-", "")

        original_transcription = transcription

        if transcription is None:
            return ""

        # Check if the text has more characters instead of punctuation marks.
        # This is the old "standardize_text" method
        transcription = html.unescape(transcription).replace("\\n", "").replace("\\t", "")
        transcription = RE_RESERVED_CHAR_FILTER.sub("", transcription)
        transcription = RE_DASH_FILTER.sub("-", transcription)
        transcription = RE_APOSTROPHE_FILTER.sub("'", transcription)
        transcription = RE_LEFT_PARENTH_FILTER.sub("(", transcription)
        transcription = RE_RIGHT_PARENTH_FILTER.sub(")", transcription)
        transcription = RE_BASIC_CLEANER.sub("", transcription)

        transcription = transcription.lstrip(LEFT_PUNCTUATION_FILTER)
        transcription = transcription.rstrip(RIGHT_PUNCTUATION_FILTER)
        transcription = transcription.translate(str.maketrans({c: f" {c} " for c in string.punctuation}))
        transcription = NORMALIZE_WHITESPACE_REGEX.sub(" ", transcription.strip())

        strip_punc = transcription.strip(string.punctuation).strip()
        no_punc = transcription.translate(str.maketrans("", "", string.punctuation)).strip()

        length_valid = (len(transcription) > 0) and (len(transcription) < max_text_length)
        text_valid = (len(strip_punc) > 1) or (len(no_punc) > 1)

        if (not length_valid) or (not text_valid) or \
                (len(tokenizer.encode(original_transcription)) <= 0):

            raise Exception(str(transcription_path) + ": " + original_transcription)

    return transcription


def read_and_preprocess_image(image_path):
    try:
        image = cv2.imread(image_path)

        if len(image.shape) == 3:
            if image.shape[2] == 4:
                trans_mask = image[:, :, 3] == 0
                image[trans_mask] = [255, 255, 255, 255]

            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return preprocess(image, input_size=OCR_INPUT_IMAGE_SHAPE)

    except:
        print("Error", image_path)


# define the parser for arguments
parser = argparse.ArgumentParser(description="Create a new HDF5 dataset from pre-existing data")

parser.add_argument('--source_path',
                    help="Path to the dataset folder",
                    required=True)

parser.add_argument('--dataset_name',  # onorio
                    help="Name of the dataset to create as an HDF5 file",
                    required=True)

# parse the passed arguments
args = parser.parse_args()
dataset_name = args.dataset_name
source_path = args.source_path
assert (os.path.isdir(source_path))

# the path of the HDF5 dataset to create
target_path = os.path.join(data_path, dataset_name + ".hdf5")

start_time = datetime.datetime.now()

# initialize the dataset dict data structure
partitions = ["train", "valid", "test"]
dataset = dict()
for partition in partitions:
    dataset[partition] = {"dt": [], "gt": []}

# Read images and sentences from the dataset
train_image_paths = sorted(Path(source_path + "/train").glob("*.jpg"))
train_transcription_paths = sorted(Path(source_path + "/train").glob("*.txt"))

valid_image_paths = sorted(Path(source_path + "/valid").glob("*.jpg"))
valid_transcription_paths = sorted(Path(source_path + "/valid").glob("*.txt"))

test_image_paths = sorted(Path(source_path + "/test").glob("*.jpg"))
test_transcription_paths = sorted(Path(source_path + "/test").glob("*.txt"))

paths = {"train": (train_image_paths, train_transcription_paths),
         "valid": (valid_image_paths, valid_transcription_paths),
         "test": (test_image_paths, test_transcription_paths)}

# read and preprocess the dataset transcriptions as "dataset ground truth" ("gt")
for partition in partitions:
    image_paths, transcription_paths = paths[partition]
    for i in range(len(image_paths)):
        cur_image_path, cur_transcription_path = image_paths[i], transcription_paths[i]

        try:
            cur_transcription = read_and_preprocess_transcription(cur_transcription_path)
            if 0 < len(cur_transcription) < max_text_length:
                dataset[partition]['gt'].append(cur_transcription)
                dataset[partition]['dt'].append(cur_image_path)
        except Exception as e:
            print(e)
            continue

# for each partition, for each couple of line image and transcription
#   - read and preprocess the line images (in a multi-process fashion for better efficiency)
#   - write the images and transcriptions in the output dataset
for partition in partitions:
    images = []

    for i in range(len(dataset[partition]['dt'])):
        if i % 100 == 0:
            print("Currently processing " + partition + " image " +
                  str(i) + "/" + str(len(dataset[partition]['dt'])) + "...")
        img = dataset[partition]['dt'][i]
        processed_image = read_and_preprocess_image(os.path.abspath(img))
        images.append(processed_image)

    with h5py.File(target_path, "w") as hf:
        hf.create_dataset(f"{partition}/dt", data=images)
        hf.create_dataset(f"{partition}/gt", data=[s.encode() for s in dataset[partition]['gt']])

total_time = datetime.datetime.now() - start_time

print(total_time)
