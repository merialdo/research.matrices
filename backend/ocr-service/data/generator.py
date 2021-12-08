"""
This module implements classes that have the responsibility to provide training/testing data.
Image renderings and text are created on the fly each time.
"""

from itertools import groupby

import data.preproc as pp
import h5py
import numpy as np
import unicodedata


class DataGenerator:
    """
    A DataGenerator has the responsibility to provide data in a streaming fashion.
    Data items are...

    """

    def __init__(self, source, batch_size, charset, max_text_length, predict=False, stream=False, lines=None):

        self.batch_size = batch_size
        self.steps = dict()
        self.index = dict()
        self.predict = predict
        self.tokenizer = Tokenizer(charset, max_text_length)

        if predict:
            self.lines = lines

        else:
            self.size = dict()

            if stream:
                self.dataset = h5py.File(source, "r")

                for partition in ['train', 'valid', 'test']:
                    self.size[partition] = self.dataset[partition]['gt'][:].shape[0]
                    self.steps[partition] = int(np.ceil(self.size[partition] / self.batch_size))
            else:
                self.dataset = dict()

                with h5py.File(source, "r") as f:
                    for partition in ['train', 'valid', 'test']:
                        self.dataset[partition] = dict()
                        self.dataset[partition]['dt'] = np.array(f[partition]['dt'])
                        self.dataset[partition]['gt'] = np.array(f[partition]['gt'])

                        self.size[partition] = len(self.dataset[partition]['gt'])
                        self.steps[partition] = int(np.ceil(self.size[partition] / self.batch_size))

            self.stream = stream
            self.arange = np.arange(len(self.dataset['train']['gt']))
            np.random.seed(42)

    def next_train_batch(self):
        """Get the next batch from train partition (yield)"""

        self.index['train'] = 0

        while True:
            if self.index['train'] >= self.size['train']:
                self.index['train'] = 0

                if not self.stream:
                    np.random.shuffle(self.arange)
                    self.dataset['train']['dt'] = self.dataset['train']['dt'][self.arange]
                    self.dataset['train']['gt'] = self.dataset['train']['gt'][self.arange]

            index = self.index['train']
            until = index + self.batch_size
            self.index['train'] = until

            x_train = self.dataset['train']['dt'][index:until]
            x_train = pp.augmentation(x_train,
                                      rotation_range=1.5,
                                      scale_range=0.05,
                                      height_shift_range=0.025,
                                      width_shift_range=0.05,
                                      erode_range=5,
                                      dilate_range=3)
            x_train = pp.normalize(x_train)

            y_train = [self.tokenizer.encode(y) for y in self.dataset['train']['gt'][index:until]]
            y_train = [np.pad(y, (0, self.tokenizer.maxlen - len(y))) for y in y_train]
            y_train = np.asarray(y_train, dtype=np.int16)

            yield (x_train, y_train)

    def next_valid_batch(self):
        """Get the next batch from validation partition (yield)"""

        self.index['valid'] = 0

        while True:
            if self.index['valid'] >= self.size['valid']:
                self.index['valid'] = 0

            index = self.index['valid']
            until = index + self.batch_size
            self.index['valid'] = until

            x_valid = self.dataset['valid']['dt'][index:until]
            x_valid = pp.normalize(x_valid)

            y_valid = [self.tokenizer.encode(y) for y in self.dataset['valid']['gt'][index:until]]
            y_valid = [np.pad(y, (0, self.tokenizer.maxlen - len(y))) for y in y_valid]
            y_valid = np.asarray(y_valid, dtype=np.int16)

            yield (x_valid, y_valid)

    def next_test_batch(self):
        """Return model predict parameters"""

        if self.predict:

            self.index['test'] = 0

            while True:
                x_test = self.lines
                x_test = pp.normalize(x_test)

                yield x_test

        else:
            self.index['test'] = 0

            while True:
                if self.index['test'] >= self.size['test']:
                    self.index['test'] = 0
                    break

                index = self.index['test']
                until = index + self.batch_size
                self.index['test'] = until

                x_test = self.dataset['test']['dt'][index:until]
                x_test = pp.normalize(x_test)

                yield x_test


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
