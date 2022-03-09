import argparse
import time
import sys
import os
import logging
import tensorflow as tf
import datetime

from backend.ocr_service.language import Language

sys.path.append(os.path.realpath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.dataset import HDF5Dataset
from backend.ocr_service.model import HTRModel
from backend.ocr_service.config import STORED_MODELS_PATH, OCR_INPUT_IMAGE_SHAPE, LANGUAGE_NAME
import backend.ocr_service.evaluation as evaluation

try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"
    logging.disable(logging.WARNING)
except AttributeError:
    pass

device_name = tf.test.gpu_device_name()

# if device_name != "/device:GPU:0":
#    raise SystemError("GPU device not found")
# print(f"Found GPU at: {device_name}")

parser = argparse.ArgumentParser(
    description="OCR model"
)

parser.add_argument('--dataset_path',
                    help="The path of the dataset to use, that must be an HDF5 file",
                    required=True)

parser.add_argument('--language',
                    type=str,
                    help="The language of the dataset.",
                    required=False)

parser.add_argument('--base_model',
                    help="The path to the base model to use",
                    required=True,
                    default=None)

parser.add_argument('--model_name',    # onorio
                    help="Name of the model to create",
                    required=True,
                    default=None)

parser.add_argument('--epochs',
                    default=100,
                    type=int,
                    help="Number of epochs.")

parser.add_argument('--learning_rate',
                    default=0.001,
                    type=float,
                    help="Learning rate")

parser.add_argument('--batch_size',
                    default=16,
                    type=int,
                    help="Number of samples in each mini-batch")

parser.add_argument('--valid',
                    default=1,
                    type=float,
                    help="Number of epochs before validation.")

# parse the passed arguments
args = parser.parse_args()
dataset_path = args.dataset_path
base_model = args.base_model
model_name = args.model_name
language_name = args.language if args.language is not None else LANGUAGE_NAME

batch_size = int(args.batch_size)
learning_rate = float(args.learning_rate)
epochs = int(args.epochs)

validation_interval = int(args.valid) if args.valid != -1 else epochs

# define input and output paths
output_model_folder_path = os.path.join(os.path.abspath(STORED_MODELS_PATH), model_name)
os.makedirs(output_model_folder_path, exist_ok=True)
checkpoint_path = os.path.join(output_model_folder_path, "checkpoint_model.{epoch:02d}.hdf5")
print("Dataset: ", dataset_path)
print("Output model folder: ", output_model_folder_path)

# define input size, number max of characters per line and list of valid characters

# load the dataset to use in training, validation and testing
dataset = HDF5Dataset(source_path=dataset_path,
                      batch_size=batch_size,
                      language=Language.from_name(language_name))
print(f"Train images:      {dataset.training_set_size}")
print(f"Validation images: {dataset.valid_set_size }")
print(f"Test images:       {dataset.test_set_size}")

# create and compile HTRModel
htr_model = HTRModel(input_size=OCR_INPUT_IMAGE_SHAPE,
                     vocabulary_size=dataset.tokenizer.vocab_size,
                     beam_width=10,
                     stop_tolerance=25,
                     reduce_tolerance=20)

htr_model.compile(learning_rate=learning_rate)
htr_model.summary(output_model_folder_path, "summary.txt")

htr_model.load_checkpoint(target=base_model)
callbacks = htr_model.get_callbacks(logdir=output_model_folder_path,
                                    checkpoint=checkpoint_path,
                                    verbose=1)

# to calculate total and average time per epoch
start_time = datetime.datetime.now()

htr_model_history = htr_model.fit(x=dataset.training_data_generator,
                                  epochs=epochs,
                                  validation_data=dataset.valid_data_generator,
                                  validation_freq=validation_interval,
                                  callbacks=callbacks,
                                  verbose=1)

training_time = datetime.datetime.now() - start_time

loss = htr_model_history.history['loss']
val_loss = htr_model_history.history['val_loss']

min_val_loss = min(val_loss)
min_val_loss_i = val_loss.index(min_val_loss)

avg_epoch_time = (training_time / len(loss))
best_epoch = (min_val_loss_i + 1) * validation_interval

t_corpus = "\n".join([
    f"Total validation images: {dataset.valid_data_generator.size}",
    f"Batch Size:              {dataset.training_data_generator.batch_size}\n",
    f"Total Training Time:     {training_time}",
    f"Time per epoch:          {avg_epoch_time}",
    f"Total epochs:            {len(loss)}",
    f"Best epoch:              {best_epoch}",
    f"Training loss:           {loss[min_val_loss_i]:.8f}",
    f"Validation loss:         {min_val_loss:.8f}"
])


with open(os.path.join(output_model_folder_path, "train.txt"), "w") as lg:
    lg.write(t_corpus)
    print(t_corpus)

start_time = time.time()

# load the checkpoint of the best epoch
best_checkpoint_path = os.path.join(output_model_folder_path, "checkpoint_model." + str(best_epoch) + ".hdf5")
htr_model.load_checkpoint(target=best_checkpoint_path)

# predict() function will return the predicts with the probabilities
predicts, prob = htr_model.predict(x=dataset.test_data_generator,
                                   steps=1,
                                   ctc_decode=True,
                                   verbose=1,
                                   use_multiprocessing=False)

print("--- %s seconds ---" % (time.time() - start_time))

predicts = tf.sparse.to_dense(predicts[0]).numpy()
prob = prob.numpy()

# decode to string
predicts = [dataset.tokenizer.decode(x) for x in predicts]
ground_truth = [x.decode() for x in dataset.test_data_generator.labels]

# mount predict corpus file
with open(os.path.join(output_model_folder_path, "predict.txt"), "w") as lg:
    for pd, gt in zip(predicts, ground_truth):
        lg.write(f"TE_L {gt}\nTE_P {pd}\n")
print(len(predicts), len(ground_truth), len(prob))

evaluate = evaluation.ocr_metrics(predicts,
                                  ground_truth,
                                  norm_accentuation=True,
                                  norm_punctuation=True)

e_corpus = "\n".join([
    f"Metrics:",
    f"Character Error Rate: {evaluate[0]:.8f}",
    f"Word Error Rate:      {evaluate[1]:.8f}",
    f"Sequence Error Rate:  {evaluate[2]:.8f}"
])

with open(os.path.join(output_model_folder_path, "evaluate.txt"), "w") as lg:
    lg.write(e_corpus)
    print(e_corpus)
