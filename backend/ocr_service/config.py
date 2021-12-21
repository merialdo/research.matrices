import string

input_size = (640, 64, 1)
charset_base = string.printable[:95]
max_text_length = 128
model_path = 'stored_models/ocr-model.hdf5'
data_path = 'data/'
