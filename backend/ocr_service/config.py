import os

OCR_ROOT = os.path.abspath(os.path.join(os.path.abspath(__file__), os.path.pardir))

STORED_MODELS_PATH = os.path.join(OCR_ROOT, 'stored_models/')
MODEL_PATH = os.path.join(STORED_MODELS_PATH, 'onorio_model.hdf5')

data_path = '/path/to/your/matrices/dataset/folder'

# OCR_INPUT_IMAGE_SHAPE = (1024, 128, 1)
OCR_INPUT_IMAGE_SHAPE = (640, 64, 1)

# OCR_MAX_TEXT_LENGTH = 128
OCR_MAX_TEXT_LENGTH = 180

LANGUAGE_NAME = "Latin"
