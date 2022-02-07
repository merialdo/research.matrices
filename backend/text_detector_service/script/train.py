import glob
import os
import cv2
import numpy as np
import os.path as osp
import datetime
from tensorflow.keras import callbacks
from tensorflow.keras import optimizers
from backend.text_detector_service.model import DBNet
from generate import generate

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# TODO: Path with train examples
training_set_path = ''

r, g, b = 0, 0, 0

files = glob.glob(training_set_path + '/*.jpg', recursive=True)

# Get List of all images
for e in files:
    image = cv2.imread(e)
    r_mean = np.mean(np.reshape(image[:, :, 0], -1))
    g_mean = np.mean(np.reshape(image[:, :, 1], -1))
    b_mean = np.mean(np.reshape(image[:, :, 2], -1))
    r += r_mean
    g += g_mean
    b += b_mean

r = r//len(files)
b = b//len(files)
g = g//len(files)

print(r, g, b)


# Dovrebbe essere lo stesso di text-detector/text_detector/config.py tranne che per la variabile MEAN
class DBConfig(object):

    STEPS_PER_EPOCH = 100

    # Number of validation steps to run at the end of every training epoch.
    # A bigger number improves accuracy of validation stats, but slows
    # down the training.
    VALIDATION_STEPS = 20

    # Backbone network architecture
    # Supported values are: ResNet50
    BACKBONE = "ResNet50"

    MEAN = [170.0, 191.0, 203.0]

    # train
    EPOCHS = 50
    INITIAL_EPOCH = 0
    PRETRAINED_MODEL_PATH = '/content/dbnet_base_model.h5'
    LOG_DIR = 'datasets/logs'
    LEARNING_RATE = 1e-4
    CHECKPOINT_DIR = os.path.join('/content/drive/MyDrive/ONORIO_DBWEIGHTS', "checkpoint_weights.{val_loss:.2f}.hdf5")

    # dataset
    IGNORE_TEXT = ["*", "###"]

    TRAIN_DATA_PATH = 'text_detector_dataset/data/train.json'
    VAL_DATA_PATH = 'text_detector_dataset/data/val.json'

    IMAGE_SIZE = 640
    BATCH_SIZE = 8

    MIN_TEXT_SIZE = 8
    SHRINK_RATIO = 0.4

    THRESH_MIN = 0.3
    THRESH_MAX = 0.7

    def __init__(self):
        """Set values of computed attributes."""

        if not osp.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)


cfg = DBConfig()

print('Start Training DBNet')
print('dataset path:', cfg.TRAIN_DATA_PATH)
print('pixels mean:', cfg.MEAN)

train_generator = generate(cfg, 'train')
val_generator = generate(cfg, 'val')

model = DBNet(cfg, model='training')

print('pretrained:', cfg.PRETRAINED_MODEL_PATH)
print('output path:', cfg.CHECKPOINT_DIR)

load_weights_path = cfg.PRETRAINED_MODEL_PATH
if load_weights_path:
    print('loading pretrained weights..')
    model.load_weights(cfg.PRETRAINED_MODEL_PATH, by_name=True, skip_mismatch=True)

model.compile(optimizer=optimizers.Adam(learning_rate=cfg.LEARNING_RATE),
              loss=[None] * len(model.output.shape))

model.summary()


checkpoint_callback = callbacks.ModelCheckpoint(
                filepath=cfg.CHECKPOINT_DIR,
                monitor="val_loss",
                save_best_only=True,
                save_weights_only=True,
                verbose=1),
reduce_lr = callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                min_delta=1e-8,
                factor=0.2,
                patience=10,
                verbose=1)
callbacks = [checkpoint_callback, reduce_lr]


model.fit(
    x=train_generator,
    steps_per_epoch=cfg.STEPS_PER_EPOCH,
    initial_epoch=cfg.INITIAL_EPOCH,
    epochs=cfg.EPOCHS,
    verbose=1,
    callbacks=callbacks,
    validation_data=val_generator,
    validation_steps=cfg.VALIDATION_STEPS
)

val = model.evaluate(val_generator, steps=10)
print(val)
