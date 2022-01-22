import h5py
import numpy as np
from tensorflow.keras.utils import Sequence
import os
import sys

sys.path.append(
    os.path.realpath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.tokenization import Tokenizer
import backend.ocr_service.image_processing as image_processing


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
                                                      batch_size=batch_size,
                                                      labels=np.array(source["valid"]['gt']),
                                                      tokenizer=self.tokenizer)
            self.valid_set_size = self.valid_data_generator.size

            self.test_data_generator = DataGenerator(samples=np.array(source["test"]['dt']),
                                                     batch_size=batch_size,
                                                     labels=np.array(source["test"]['gt']),
                                                     tokenizer=self.tokenizer)
            self.test_set_size = self.test_data_generator.size


class DataGenerator(Sequence):

    def __init__(self,
                 samples: np.array,
                 labels: np.array,
                 batch_size: int,
                 tokenizer: Tokenizer):
        self.samples = samples
        self.labels = labels
        self.tokenizer = tokenizer

        self.batch_size = batch_size
        self.current_epoch = 0

        self.size = len(self.labels)
        self.steps_number = int(np.ceil(self.size / self.batch_size))

    def __len__(self):
        """
        Denote the number of batches per epoch
        """
        return self.steps_number

    def __getitem__(self, index):
        """
        Generate the next batch of validation data.
        """

        x_valid = self.samples[index * self.batch_size:(index + 1) * self.batch_size]
        x_valid = image_processing.normalize(x_valid)

        y_valid = self.labels[index * self.batch_size:(index + 1) * self.batch_size]
        y_valid = [self.tokenizer.encode(y) for y in y_valid]
        y_valid = [np.pad(y, (0, self.tokenizer.maxlen - len(y))) for y in y_valid]
        y_valid = np.asarray(y_valid, dtype=np.int16)

        return x_valid, y_valid

    def on_epoch_end(self):
        """
        Update indexes after each epoch
        """
        self.current_epoch += 1


class TrainingDataGenerator(DataGenerator):

    def __init__(self,
                 samples: np.array,
                 labels: np.array,
                 batch_size: int,
                 tokenizer: Tokenizer):
        # the DataGenerator initializer will save and initialize
        # samples, labels, tokenizer, batch_size, current_epoch, size and step_number

        super().__init__(samples=samples,
                         labels=labels,
                         batch_size=batch_size,
                         tokenizer=tokenizer)

        # this will be useful to shuffle the samples and labels at the end of each epoch
        self.arange = np.arange(len(self.labels))
        np.random.seed(42)

    # override the DataGenerator __getitem__ in order to also perform augmentation
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

    # override the DataGenerator on_epoch_end method to shuffle the samples and labels
    def on_epoch_end(self):
        """
        Update indexes after each epoch
        """
        self.current_epoch += 1

        np.random.shuffle(self.arange)
        self.samples = self.samples[self.arange]
        self.labels = self.labels[self.arange]
