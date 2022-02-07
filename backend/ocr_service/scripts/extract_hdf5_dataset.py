import os

import h5py
import numpy as np
import cv2

source_path = "/Users/andrea/matrices_dataset/biagini.hdf5"
output_root = "/Users/andrea/matrices_dataset/biagini"



def trim_grayscale_image(image):
    image_neg = cv2.bitwise_not(image)  # invert the root to white
    coords = cv2.findNonZero(image_neg)  # find all the non-zero points (root)
    x, y, w, h = cv2.boundingRect(coords)  # find minimum spanning bounding box
    rect = image[y:y + h, x:x + w]
    return rect

with h5py.File(source_path, "r") as source:

    for partition in ["valid"]:
        output_folder = os.path.join(output_root, partition)
        os.makedirs(output_folder, exist_ok=True)

        print("Partition: " + partition)

        samples = source[partition]['dt']
        labels = np.array(source[partition]['gt'])

        for i in range(len(labels)):
            if i % 100 == 0:
                print("\t" + str(i))

            try:
                cur_image = trim_grayscale_image(np.array(samples[i]))
                cv2.imwrite(os.path.join(output_folder, str(i) + ".jpg"), cur_image.transpose())
                cur_label = labels[i]
                with open(os.path.join(output_folder, str(i) + ".jpg.txt"), "w") as outlabel:
                    outlabel.writelines(cur_label.decode())

            except Exception:
                pass
