"""Dataset reader and process"""

import os
import string
import random
import multiprocessing
from glob import glob
from tqdm import tqdm
import preproc as pp
from functools import partial
from pathlib import Path
import numpy as np
import h5py
from itertools import groupby
import unicodedata
import re


class Tokenizer:
    """Manager tokens functions and charset/dictionary properties"""

    def __init__(self, chars, max_text_length=128):
        self.PAD_TK, self.UNK_TK = "¶", "¤"
        self.chars = (self.PAD_TK + self.UNK_TK + chars)

        self.PAD = self.chars.find(self.PAD_TK)
        self.UNK = self.chars.find(self.UNK_TK)

        self.vocab_size = len(self.chars)
        self.maxlen = max_text_length

    def encode(self, text):
        """Encode text to vector"""

        if isinstance(text, bytes):
            text = text.decode()

        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
        text = " ".join(text.split())

        groups = ["".join(group) for _, group in groupby(text)]
        text = "".join([self.UNK_TK.join(list(x)) if len(x) > 1 else x for x in groups])
        encoded = []

        for item in text:
            index = self.chars.find(item)

            index = self.UNK if index == -1 else index
            encoded.append(index)

        return np.asarray(encoded)

    def decode(self, text):
        """Decode vector to text"""

        decoded = "".join([self.chars[int(x)] for x in text if x > -1])
        decoded = self.remove_tokens(decoded)

        return decoded

    def remove_tokens(self, text):
        """Remove tokens (PAD) from text"""

        return text.replace(self.PAD_TK, "").replace(self.UNK_TK, "")


class Dataset:
    """Dataset class to read images and sentences from base (raw files)"""

    def __init__(self, source, name):
        self.source = source
        self.name = name
        self.dataset = None
        self.partitions = ['train', 'valid', 'test']

    def read_partitions(self):
        """Read images and sentences from dataset"""

        dataset = getattr(self, f"_{self.name}")()

        if not self.dataset:
            self.dataset = self._init_dataset()

        for y in self.partitions:
            self.dataset[y]['dt'] += dataset[y]['dt']
            self.dataset[y]['gt'] += dataset[y]['gt']

    def save_partitions(self, target, image_input_size, max_text_length):
        """Save images and sentences from dataset"""

        os.makedirs(os.path.dirname(target), exist_ok=True)
        total = 0

        with h5py.File(target, "w") as hf:
            for pt in self.partitions:
                self.dataset[pt] = self.check_text(self.dataset[pt], max_text_length)
                size = (len(self.dataset[pt]['dt']),) + image_input_size[:2]
                total += size[0]

                dummy_image = np.zeros(size, dtype=np.uint8)
                dummy_sentence = [("c" * max_text_length).encode()] * size[0]
                print("Size", size)
                hf.create_dataset(f"{pt}/dt", data=dummy_image, compression="gzip", compression_opts=9)
                hf.create_dataset(f"{pt}/gt", data=dummy_sentence, compression="gzip", compression_opts=9)

        pbar = tqdm(total=total)
        batch_size = 60

        for pt in self.partitions:
            for batch in range(0, len(self.dataset[pt]['gt']), batch_size):
                images = []

                with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                    r = pool.map(partial(pp.preprocess, input_size=image_input_size),
                                 self.dataset[pt]['dt'][batch:batch + batch_size])
                    images.append(r)
                    pool.close()
                    pool.join()

                with h5py.File(target, "a") as hf:
                    hf[f"{pt}/dt"][batch:batch + batch_size] = images
                    hf[f"{pt}/gt"][batch:batch + batch_size] = [s.encode() for s in
                                                                self.dataset[pt]['gt'][batch:batch + batch_size]]
                    pbar.update(batch_size)

    def _init_dataset(self):
        dataset = dict()

        for i in self.partitions:
            dataset[i] = {"dt": [], "gt": []}

        return dataset

    def _shuffle(self, *ls):
        random.seed(42)

        if len(ls) == 1:
            li = list(*ls)
            random.shuffle(li)
            return li

        li = list(zip(*ls))
        random.shuffle(li)
        return zip(*li)

    def _verbali(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        dataset = self._init_dataset()
        train = [(line, gt[i]) for i, line in enumerate(paths)]
        test = [(line, gt[i]) for i, line in enumerate(paths) if i % 10 == 0]
        valid = test
        train = [item for item in train if item not in valid]
        train = [item for item in train if item not in test]
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if len(g) > 0:
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def _coco(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        dataset = self._init_dataset()
        train, valid, test = [], [], []
        for i, (line, gt) in enumerate(zip(paths, gt)):
            if i % 5 == 0:
                test.append((line, gt))
            else:
                train.append((line, gt))

        valid = test

        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if len(g) > 0:
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def check_test(self, s, test_list):
        for s_test in test_list:
            if s_test in s:
                return True
        return False

    def check_disp(self, s):
        if "displacement" in s:
            return False
        else:
            return True

    def _ocr_targhe(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        test_list = []
        with open("test_list.txt", "r") as test_file:
            for elem in test_file.readlines():
                test_list.append(elem.strip().split(".jpg")[0])

        dataset = self._init_dataset()
        all_data = [(line, gt[i]) for i, line in enumerate(paths)]
        test = []
        train = []
        for line, gt in all_data:
            name = line.split("/")[-1].split(".jpg")[0]
            if self.check_test(name, test_list) and self.check_disp(name):
                test.append((line, gt))
            elif self.check_test(name, test_list) and not self.check_disp(name):
                continue
            else:
                train.append((line, gt))

        valid = test
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                print(line)
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if len(g) > 0:
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def _petizioni(self):
        """Petizioni Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.png")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        dataset = self._init_dataset()
        train = [(line, gt[i]) for i, line in enumerate(paths)]
        test = [(line, gt[i]) for i, line in enumerate(paths) if i % 95 == 0]
        train = [item for item in train if item not in test]
        valid = test
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    gt = gt.read().splitlines()[0].strip()
                    if len(gt) > 0:
                        dataset[i]['gt'].append(gt)
                        dataset[i]['dt'].append(line[0])

        return dataset

    def _onorio(self):
        """onorio"""

        paths_train = sorted(Path(self.source + "/train").glob("*.jpg"))
        gt_train = sorted(Path(self.source + "/train").glob("*.txt"))

        paths_test = sorted(Path(self.source + "/test").glob("*.jpg"))
        gt_test = sorted(Path(self.source + "/test").glob("*.txt"))

        dataset = self._init_dataset()
        train = [(str(line), str(gt_train[i])) for i, line in enumerate(paths_train)]
        test = [(str(line), str(gt_test[i])) for i, line in enumerate(paths_test)]
        valid = test

        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    gt = gt.read().splitlines()[0].strip()
                    gt = gt.replace("(", "").replace(")", "").replace("'", "")
                    gt = re.sub("\{.*?\}", "", gt)
                    gt = re.sub("\[.*?\]", "", gt)
                    gt = gt.replace("-", "")
                    if len(gt) > 0:
                        dataset[i]['gt'].append(gt)
                        dataset[i]['dt'].append(line[0])

        return dataset

    @staticmethod
    def check_text(data, max_text_length=180):
        """Checks if the text has more characters instead of punctuation marks"""
        alph = string.digits + string.ascii_letters + string.punctuation + '°' + 'àâéèêëîïôùûçÀÂÉÈËÎÏÔÙÛÇ' + '£€¥¢฿ '
        tokenizer = Tokenizer(alph, max_text_length)

        for i in reversed(range(len(data['gt']))):
            text = pp.text_standardize(data['gt'][i])
            strip_punc = text.strip(string.punctuation).strip()
            no_punc = text.translate(str.maketrans("", "", string.punctuation)).strip()

            length_valid = (len(text) > 0) and (len(text) < max_text_length)
            text_valid = (len(strip_punc) > 1) or (len(no_punc) > 1)

            if (not length_valid) or (not text_valid) or (len(tokenizer.encode(data['gt'][i])) <= 0):
                print("Error", data['gt'][i])
                data['gt'].pop(i)
                data['dt'].pop(i)

        return data