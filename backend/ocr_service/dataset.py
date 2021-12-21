import h5py
import numpy as np
from tensorflow.python.keras.utils.data_utils import Sequence
import unicodedata
from itertools import groupby
import os
import sys
sys.path.append(os.path.realpath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir)))

import backend.ocr_service.image_processing as image_processing


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
        # if (self.check_carplates(text)):
        #    text = text[:2] + " " + text[2:]
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


class HDF5Dataset:
    def __init__(self, source_path, charset, max_text_length, batch_size):
        self.source_path = source_path
        self.tokenizer = Tokenizer(charset, max_text_length)
        self.training_batch_size = batch_size

        with h5py.File(self.source_path, "r") as source:
            self.training_data_generator = TrainingDataGenerator(samples=np.array(source["train"]['dt']),
                                                                 labels=np.array(source["train"]['gt']),
                                                                 batch_size=batch_size,
                                                                 tokenizer=self.tokenizer)
            self.training_set_size = self.training_data_generator.size

            self.valid_data_generator = DataGenerator(samples=np.array(source["valid"]['dt']),
                                                      labels=np.array(source["valid"]['gt']),
                                                      tokenizer=self.tokenizer)
            self.valid_set_size = self.valid_data_generator.size

            self.test_data_generator = DataGenerator(samples=np.array(source["test"]['dt']),
                                                     labels=np.array(source["test"]['gt']),
                                                     tokenizer=self.tokenizer)
            self.test_set_size = self.test_data_generator.size


class DataGenerator(Sequence):

    def __init__(self,
                 samples: np.array,
                 labels: np.array,
                 tokenizer: Tokenizer):

        self.samples = samples
        self.labels = labels
        self.tokenizer = tokenizer

        self.batch_size = len(labels)
        self.steps_number = 1
        self.size = len(self.labels)

    def __len__(self):
        """
        Denote the number of batches per epoch
        """
        return self.steps_number

    def __getitem__(self, index):
        """
        Generate one batch of data
        """
        x_valid = image_processing.normalize(self.samples)

        y_valid = [self.tokenizer.encode(y) for y in self.labels]
        y_valid = [np.pad(y, (0, self.tokenizer.maxlen - len(y))) for y in y_valid]
        y_valid = np.asarray(y_valid, dtype=np.int16)

        return x_valid, y_valid

    def on_epoch_end(self):
        """
        Update indexes after each epoch
        """
        pass


class TrainingDataGenerator(DataGenerator):

    def __init__(self,
                 samples: np.array,
                 labels: np.array,
                 batch_size: int,
                 tokenizer: Tokenizer):

        # the DataGenerator initializer will save samples, labels and tokenizer
        super().__init__(samples, labels, tokenizer)

        self.batch_size = batch_size
        self.current_epoch = 0

        self.size = len(self.labels)
        self.steps_number = int(np.ceil(self.size / self.batch_size))

        self.arange = np.arange(len(self.labels))
        np.random.seed(42)

    def __len__(self):
        """
        Denote the number of batches per epoch
        """
        return self.steps_number

    def __getitem__(self, index):
        """
        Generate the next batch of training data.
        Augment the X
        """
        x_train = self.samples[index * self.batch_size:(index + 1) * self.batch_size]
        y_train = self.labels[index * self.batch_size:(index + 1) * self.batch_size]

        x_train = image_processing.manual_augmentation(x_train,
                                                       rotation_range=0.5,
                                                       scale_range=0.02,
                                                       height_shift_range=0.02,
                                                       width_shift_range=0.01,
                                                       erode_range=3,
                                                       dilate_range=3)
        x_train = image_processing.albumentations_augmentation(x_train)
        x_train = image_processing.normalize(x_train)

        y_train = [self.tokenizer.encode(y) for y in y_train]
        y_train = [np.pad(y, (0, self.tokenizer.maxlen - len(y))) for y in y_train]
        y_train = np.asarray(y_train, dtype=np.int16)

        return x_train, y_train

    def on_epoch_end(self):
        """
        Update indexes after each epoch
        """
        self.current_epoch += 1

        np.random.shuffle(self.arange)
        self.samples = self.samples[self.arange]
        self.labels = self.labels[self.arange]
