import argparse
import sys
import os
import logging
import tensorflow as tf

sys.path.append(os.path.realpath(os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.ocr_service.dataset import HDF5Dataset
from backend.ocr_service.model import HTRModel
from backend.ocr_service.config import OCR_INPUT_IMAGE_SHAPE, OCR_MAX_TEXT_LENGTH, CHARSET_BASE, data_path
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

parser.add_argument('--dataset',        # onorio
                    help="Name of the dataset to use, as an HDF5 file",
                    required=True)

parser.add_argument('--model_path',    # onorio
                    help="Path to the model checkpoint to load",
                    required=True)

# parse the passed arguments
args = parser.parse_args()
dataset_name = args.dataset
model_path = args.model_path

# define input and output paths
dataset_path = os.path.join(os.path.abspath(data_path), dataset_name + ".hdf5")

# load the dataset to use in training, validation and testing
dataset = HDF5Dataset(source_path=dataset_path,
                      batch_size=16,
                      charset=CHARSET_BASE,
                      max_text_length=OCR_MAX_TEXT_LENGTH)
print(f"Train images:      {dataset.training_set_size}")
print(f"Validation images: {dataset.valid_set_size }")
print(f"Test images:       {dataset.test_set_size}")

# create and compile HTRModel
htr_model = HTRModel(input_size=OCR_INPUT_IMAGE_SHAPE,
                     vocabulary_size=dataset.tokenizer.vocab_size,
                     beam_width=10,
                     stop_tolerance=25,
                     reduce_tolerance=20)

htr_model.compile(learning_rate=0.001)
htr_model.load_checkpoint(target=model_path)

# predict() function will return the predicts with the probabilities
predicts, prob = htr_model.predict(x=dataset.test_data_generator,
                                   batch_size=16,
                                   steps=1,
                                   ctc_decode=True,
                                   verbose=1,
                                   use_multiprocessing=False)

predicts = tf.sparse.to_dense(predicts[0]).numpy()
prob = prob.numpy()

# decode to string
predicts = [dataset.tokenizer.decode(x) for x in predicts]
ground_truth = [x.decode() for x in dataset.test_data_generator.labels]
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

print(e_corpus)
