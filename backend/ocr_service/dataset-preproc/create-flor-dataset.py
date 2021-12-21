import datetime
from reader import Dataset
import os

if __name__ == '__main__':

    input_size = (640, 64, 1)
    max_text_length = 180

    start_time = datetime.datetime.now()

    ds = Dataset(source="./ocr_dataset/", name='onorio')
    ds.read_partitions()

    source_path = os.path.join("dataset", "onorio.hdf5")
    print("Partitions will be preprocessed and saved...")
    ds.save_partitions(source_path, input_size, max_text_length)

    total_time = datetime.datetime.now() - start_time

    print(total_time)
