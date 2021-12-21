"""
Image processing functions:
    adjust_to_see: adjust an image to better visualize it (rotate and transpose)
    augmentation: apply variations to a list of images
    normalization: apply normalization and variations on images (if required)
    preprocess: main function for image preprocessing before
    text_standardize: preprocess and standardize sentence
"""

import cv2
import numpy as np
import albumentations

AUGMENTATIONS_TRAIN = albumentations.Compose([

    albumentations.OneOf([
        # A.Rotate(limit=[1,1],interpolation=cv2.INTER_NEAREST,border_mode=cv2.BORDER_CONSTANT),
        # A.RandomBrightnessContrast(),
        # A.IAAAdditiveGaussianNoise(),
        # A.GaussNoise(),
        # JpegCompression(quality_lower=99, quality_upper=100, always_apply=False),
        albumentations.Cutout(num_holes=5, max_h_size=4, max_w_size=4),
        albumentations.Cutout(num_holes=20, max_h_size=1, max_w_size=1),
        # ShiftScaleRotate(shift_limit=0.05, scale_limit=0.06,rotate_limit=1.6, border_mode=BORDER_CONSTANT),
    ], p=1),
])


def manual_augmentation(imgs,
                        rotation_range=0,
                        scale_range=0,
                        height_shift_range=0,
                        width_shift_range=0,
                        dilate_range=1,
                        erode_range=1):
    """Apply variations to a list of images (rotate, width and height shift, scale, erode, dilate)"""

    imgs = imgs.astype(np.float32)
    _, h, w = imgs.shape

    dilate_kernel = np.ones((int(np.random.uniform(1, dilate_range)),), np.uint8)
    erode_kernel = np.ones((int(np.random.uniform(1, erode_range)),), np.uint8)
    height_shift = np.random.uniform(-height_shift_range, height_shift_range)
    rotation = np.random.uniform(-rotation_range, rotation_range)
    scale = np.random.uniform(1 - scale_range, 1)
    width_shift = np.random.uniform(-width_shift_range, width_shift_range)

    trans_map = np.float32([[1, 0, width_shift * w], [0, 1, height_shift * h]])
    rot_map = cv2.getRotationMatrix2D((w // 2, h // 2), rotation, scale)

    trans_map_aff = np.r_[trans_map, [[0, 0, 1]]]
    rot_map_aff = np.r_[rot_map, [[0, 0, 1]]]
    affine_mat = rot_map_aff.dot(trans_map_aff)[:2, :]

    for i in range(len(imgs)):
        imgs[i] = cv2.warpAffine(imgs[i], affine_mat, (w, h), flags=cv2.INTER_NEAREST, borderValue=255)
        imgs[i] = cv2.erode(imgs[i], erode_kernel, iterations=1)
        imgs[i] = cv2.dilate(imgs[i], dilate_kernel, iterations=1)

    return imgs


def albumentations_augmentation(x_train):
    transform = AUGMENTATIONS_TRAIN
    batch = []
    for x in x_train:
        x_transformed = transform(image=x)
        x_transformed = x_transformed["image"]
        batch.append(np.array(x_transformed))

    return np.array(batch)


def adjust_to_see(img):
    """Rotate and transpose to image visualize (cv2 method or jupyter notebook)"""

    (h, w) = img.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D((cX, cY), -90, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])

    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))

    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY

    img = cv2.warpAffine(img, M, (nW + 1, nH + 1))
    img = cv2.warpAffine(img.transpose(), M, (nW, nH))

    return img


def normalize(images: list):
    """Normalize a list of images
    (typically a batch of images of lines to transcribe)"""

    normalized_images = np.asarray(images).astype(np.float32)
    normalized_images = np.expand_dims(normalized_images / 255, axis=-1)

    return normalized_images


def preprocess(image, input_size):
    """
    Preprocess metodology based in:
        H. Scheidl, S. Fiel and R. Sablatnig,
        Word Beam Search: A Connectionist Temporal Classification Decoding Algorithm, in
        16th International Conference on Frontiers in Handwriting Recognition, pp. 256-258, 2018.

    :param image: the grayscale image of a line
    :param input_size:
    """

    # separate image from background
    u, i = np.unique(np.array(image).flatten(), return_inverse=True)
    background = int(u[np.argmax(np.bincount(i))])

    wt, ht, _ = input_size
    h, w = np.asarray(image).shape
    f = max((w / wt), (h / ht))

    new_size = (max(min(wt, int(w / f)), 1), max(min(ht, int(h / f)), 1))
    img = cv2.resize(image, new_size)

    target = np.ones([ht, wt], dtype=np.uint8) * background
    target[0:new_size[1], 0:new_size[0]] = img
    img = cv2.transpose(target)

    return img
