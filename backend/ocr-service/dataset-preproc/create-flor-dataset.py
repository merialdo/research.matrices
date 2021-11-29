'''
from pathlib import Path
import shutil, os
import re
import cv2
import numpy as np
import math
from tqdm import tqdm
import preproc as pp
images_train = list(sorted(thPath("1040/3").glob("**/*.jpg")))
input_size = (640, 64, 1)

for elem in images_train[:10]:
    img = cv2.imread(str(elem),cv2.IMREAD_GRAYSCALE)
    preproc = pp.preprocess(img,input_size)
    cv2.imshow("exe",pp.adjust_to_see(preproc))
    cv2.waitKey(0)

'''

import datetime
from reader import Dataset
import os
start_time = datetime.datetime.now()

if __name__ == '__main__':

    input_size = (640 , 64 , 1)
    max_text_length = 180

    ds = Dataset(source="./ocr_dataset/" , name='onorio')
    ds.read_partitions()
    source_path = os.path.join("dataset" , "onorio.hdf5")
    print("Partitions will be preprocessed and saved...")
    ds.save_partitions(source_path , input_size , max_text_length)

    total_time = datetime.datetime.now() - start_time

    print(total_time)
