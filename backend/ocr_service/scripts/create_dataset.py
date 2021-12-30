import argparse
import datetime
import html
import multiprocessing
import os
import re
import string
from functools import partial
from pathlib import Path
import cv2
import h5py
import numpy
import sys
from tqdm import tqdm

sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.config import OCR_INPUT_IMAGE_SHAPE, OCR_MAX_TEXT_LENGTH, data_path
from backend.ocr_service.tokenization import Tokenizer

# define some important assets
alphabet = string.digits + string.ascii_letters + string.punctuation + '°' + 'àâéèêëîïôùûçÀÂÉÈËÎÏÔÙÛÇ' + '£€¥¢฿ '
tokenizer = Tokenizer(alphabet, OCR_MAX_TEXT_LENGTH)

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


def check_text(text):
    """This method checks if the text has any characters other than punctuation marks;
    if it does, it returns True, otherwise it returns False"""
    original_text = text

    if text is None:
        return False

    text = html.unescape(text).replace("\\n", "").replace("\\t", "")

    text = RE_RESERVED_CHAR_FILTER.sub("", text)
    text = RE_DASH_FILTER.sub("-", text)
    text = RE_APOSTROPHE_FILTER.sub("'", text)
    text = RE_LEFT_PARENTH_FILTER.sub("(", text)
    text = RE_RIGHT_PARENTH_FILTER.sub(")", text)
    text = RE_BASIC_CLEANER.sub("", text)

    text = text.lstrip(LEFT_PUNCTUATION_FILTER)
    text = text.rstrip(RIGHT_PUNCTUATION_FILTER)
    text = text.translate(str.maketrans({c: f" {c} " for c in string.punctuation}))
    text = NORMALIZE_WHITESPACE_REGEX.sub(" ", text.strip())

    strip_punc = text.strip(string.punctuation).strip()
    no_punc = text.translate(str.maketrans("", "", string.punctuation)).strip()

    length_valid = (len(text) > 0) and (len(text) < OCR_MAX_TEXT_LENGTH)
    text_valid = (len(strip_punc) > 1) or (len(no_punc) > 1)

    return length_valid and text_valid and len(tokenizer.encode(original_text)) > 0


def read_and_preprocess_transcription(transcription_path):
    with open(transcription_path, 'r', encoding='latin-1') as transcription_input:
        transcription = transcription_input.read().splitlines()[0].strip()
        transcription = transcription.replace("(", "").replace(")", "").replace("'", "")
        transcription = re.sub("\{.*?\}", "", transcription)
        transcription = re.sub("\[.*?\]", "", transcription)
        transcription = transcription.replace("-", "")

        if not check_text(transcription):
            raise Exception("Error in transcription " + str(transcription_path) + ":\n\t" + transcription)

    return transcription


def read_and_preprocess_image(image_path):
    """Make the process with the `input_size` to the scale resize"""

    try:
        read_image = cv2.imread(image_path)

        if len(read_image.shape) == 3:
            if read_image.shape[2] == 4:
                trans_mask = read_image[:, :, 3] == 0
                read_image[trans_mask] = [255, 255, 255, 255]

            read_image = cv2.cvtColor(read_image, cv2.COLOR_BGR2GRAY)

        # actual preprocessing (identical to the one in image_preprocessing)
        wt, ht, _ = OCR_INPUT_IMAGE_SHAPE
        h, w = numpy.asarray(read_image).shape
        f = max((w / wt), (h / ht))
        new_size = (max(min(wt, int(w / f)), 1), max(min(ht, int(h / f)), 1))

        image = cv2.resize(read_image, new_size)

        target = numpy.ones([ht, wt], dtype=numpy.uint8) * 255
        target[0:new_size[1], 0:new_size[0]] = image
        image = cv2.transpose(target)
        return image

    except:
        print("Error", image_path)


if __name__ == '__main__':

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
            cur_image_path, cur_transcription_path = os.path.abspath(image_paths[i]), os.path.abspath(transcription_paths[i])

            try:
                cur_transcription = read_and_preprocess_transcription(cur_transcription_path)
                if 0 < len(cur_transcription) < OCR_MAX_TEXT_LENGTH:
                    dataset[partition]['gt'].append(cur_transcription)
                    dataset[partition]['dt'].append(cur_image_path)
            except Exception as e:
                print(e)
                continue

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    total = 0

    with h5py.File(target_path, "w") as hf:
        for partition in partitions:
            size = (len(dataset[partition]['dt']),) + OCR_INPUT_IMAGE_SHAPE[:2]
            total += size[0]

            dummy_image = numpy.zeros(size, dtype=numpy.uint8)
            dummy_sentence = [("c" * OCR_MAX_TEXT_LENGTH).encode()] * size[0]
            print("Size", size)
            hf.create_dataset(f"{partition}/dt", data=dummy_image, compression="gzip", compression_opts=9)
            hf.create_dataset(f"{partition}/gt", data=dummy_sentence, compression="gzip", compression_opts=9)

    pbar = tqdm(total=total)
    batch_size = 60

    # for each partition, for each couple of line image and transcription
    #   - read and preprocess the line images (in a multi-process fashion for better efficiency)
    #   - write the images and transcriptions in the output dataset
    for partition in partitions:
        for batch in range(0, len(dataset[partition]['gt']), batch_size):
            images = []

            with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                r = pool.map(partial(read_and_preprocess_image),
                             dataset[partition]['dt'][batch:batch + batch_size])
                images.append(r)
                pool.close()
                pool.join()

            with h5py.File(target_path, "a") as hf:
                hf[f"{partition}/dt"][batch:batch + batch_size] = images
                hf[f"{partition}/gt"][batch:batch + batch_size] = [s.encode() for s in
                                                            dataset[partition]['gt'][batch:batch + batch_size]]
                pbar.update(batch_size)

    total_time = datetime.datetime.now() - start_time

    print(total_time)
