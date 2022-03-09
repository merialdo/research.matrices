import argparse
import datetime
import os
from pathlib import Path
import cv2
import h5py
import numpy
import sys
from tqdm import tqdm

sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.config import OCR_INPUT_IMAGE_SHAPE, OCR_MAX_TEXT_LENGTH, data_path
from backend.ocr_service.language import Language
from backend.ocr_service.cleaning import Cleaner


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

    parser.add_argument('--language',  # Latin
                        help="The dataset language: it affects the cleaning and tokenization processes",
                        required=True)

    parser.add_argument('--dataset_name',  # onorio
                        help="Name of the dataset to create as an HDF5 file",
                        required=True)

    # parse the passed arguments
    args = parser.parse_args()
    dataset_name = args.dataset_name
    language_name = args.language
    source_path = args.source_path
    assert (os.path.isdir(source_path))

    language = Language.from_name(language_name)

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

    test_image_paths = sorted(Path(source_path + "/test").glob("*.jpg"))
    test_transcription_paths = sorted(Path(source_path + "/test").glob("*.txt"))

    if os.path.isdir(source_path + "/valid"):
        valid_image_paths = sorted(Path(source_path + "/valid").glob("*.jpg"))
        valid_transcription_paths = sorted(Path(source_path + "/valid").glob("*.txt"))
    else:
        valid_image_paths = test_image_paths
        valid_transcription_paths = test_transcription_paths

    paths = {"train": (train_image_paths, train_transcription_paths),
             "valid": (valid_image_paths, valid_transcription_paths),
             "test": (test_image_paths, test_transcription_paths)}

    # read and clean/preprocess the dataset transcriptions as "dataset ground truth" ("gt")
    cleaner = Cleaner.for_language(language)
    for partition in partitions:
        image_paths, transcription_paths = paths[partition]
        for i in range(len(image_paths)):
            cur_image_path = os.path.abspath(image_paths[i])
            cur_transcription_path = cur_image_path+".txt"
            assert(os.path.isfile(cur_transcription_path))
            assert(os.path.isfile(cur_image_path))

            with open(cur_transcription_path, 'r') as cur_transcription_file:
                cur_transcription = cur_transcription_file.readlines()[0].strip()
                cur_transcription = cleaner.clean(cur_transcription)
                if not cleaner.is_acceptable(cur_transcription):
                    print("Encountered an error with sample: " + cur_transcription_path)
                    print("Clean transcription: " + cur_transcription)
                    continue

                if 0 < len(cur_transcription) < OCR_MAX_TEXT_LENGTH:
                    dataset[partition]['gt'].append(cur_transcription)
                    dataset[partition]['dt'].append(cur_image_path)

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

            #with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            #    r = pool.map(partial(read_and_preprocess_image),
            #                 dataset[partition]['dt'][batch:batch + batch_size])
            #    images.append(r)
            #    pool.close()
            #    pool.join()

            with h5py.File(target_path, "a") as hf:
                hf[f"{partition}/dt"][batch:batch + batch_size] = [read_and_preprocess_image(im) for im in
                                                                   dataset[partition]['dt'][batch:batch + batch_size]]
                hf[f"{partition}/gt"][batch:batch + batch_size] = [s.encode() for s in
                                                                   dataset[partition]['gt'][batch:batch + batch_size]]

                pbar.update(batch_size)

    total_time = datetime.datetime.now() - start_time

    print(total_time)
