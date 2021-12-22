import string
import os

input_size = (640, 64, 1)
charset_base = string.printable[:95]
max_text_length = 128

OCR_ROOT = os.path.abspath(os.curdir)
STORED_MODELS_PATH = os.path.join(OCR_ROOT, 'stored_models/')
MODEL_PATH = os.path.join(STORED_MODELS_PATH, 'checkpoint_weights.32.43.hdf5')
data_path = '/Users/andrea/matrices_dataset/'
