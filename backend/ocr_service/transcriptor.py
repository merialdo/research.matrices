import numpy as np
import tensorflow as tf
import cv2
from dataset import Tokenizer
from image_processing import normalize, preprocess
from model import HTRModel


class Transcriptor:

    def __init__(self,
                 model_path: str,
                 input_image_size: tuple,
                 max_text_length: int,
                 charset):

        self.model_path = model_path
        self.input_image_size = input_image_size
        self.max_text_length = max_text_length
        self.charset = charset

        self.tokenizer = Tokenizer(charset, max_text_length)

        self.model = self._load_model(input_size=input_image_size,
                                      vocabulary_size=self.tokenizer.vocab_size,
                                      model_path=model_path)

    def _load_model(self, input_size, vocabulary_size, model_path):
        model = HTRModel(input_size=input_size,
                         vocabulary_size=vocabulary_size,
                         beam_width=0,
                         greedy=True)

        print('Loading model from location ' + model_path, '...')
        model.load_checkpoint(target=model_path)
        print('Done.')

        return model

    def transcribe(self, page_image, bounding_boxes):

        line_images = []

        # for each passed bounding box (i.e., each line to transcribe), crop the corresponding line image:
        for current_box in bounding_boxes:
            cur_box_x, cur_box_y, cur_box_width, cur_box_height = current_box

            # use the bounding box coordinates to extract the line image
            line_image = page_image[cur_box_y:cur_box_y + cur_box_height, cur_box_x:cur_box_x + cur_box_width]

            # preprocess the line image
            preprocessed_line_image = preprocess(line_image, self.input_image_size)

            # append the result to the list of line images
            line_images.append(preprocessed_line_image)

        # this is where the actual transcription process takes place
        predictions = []
        probabilities = []
        print('Number of lines to transcribe: ' + str(len(line_images)))

        # work in batches of 64 lines each;
        # for each batch, run the predict method of the loaded model
        # (which is defined in the outer scope of the file, so it is visible)
        batch_start = 0
        batch_size = 64

        while batch_start < len(line_images):
            cur_batch = line_images[batch_start: min(batch_start + batch_size, len(line_images))]

            cur_batch_predictions, cur_batch_probabilities = self.model.predict(normalize(cur_batch),
                                                                                ctc_decode=True,
                                                                                verbose=1, )
            predictions.extend(cur_batch_predictions)
            probabilities.extend(cur_batch_probabilities)
            batch_start += batch_size

        # some post-processing
        predictions = tf.sparse.to_dense(predictions[0]).numpy()
        probabilities = [prob.numpy() for prob in probabilities]
        probabilities = [str(np.exp(prob[0])) for prob in probabilities]

        # decode the predictions into actual string transcriptions
        transcriptions = [self.tokenizer.decode(x) for x in predictions]

        return transcriptions, probabilities


def rescale_points(point_list: list,
                   w_ratio: float,
                   h_ratio: float) -> np.array:
    """
    This utility method recomputes the coordinates of a list of points
    by scaling them according to the passed width ratio and height ratio.


    @param: point_list: The list of points to rescale
    @param: w_ratio: The horizontal axis rescaling factor
    @param: h_ratio: The vertical axis rescaling factor

    @returns: a numpy array with the rescaled points
    """
    resized_points = []
    for point in point_list:
        x, y = point[0], point[1]
        resized_x, resized_y = int(x * w_ratio), int(y * h_ratio)
        resized_point = (resized_x, resized_y)
        resized_points.append(resized_point)

    resized_points = np.array(resized_points, dtype=np.int32)
    return resized_points


def resize_image_from_short_side(image,
                                 short_side_target_size: int):
    """
    This utility method rescales a rectangular OpenCV image
    by resizing its short side to a passed target size
    (and rescaling the other side accordingly)

    @param: image: an image to resize
    @param: short_side_target_size: the size that we want the short side of the image to have,
                                    after the image is resized

    @return: the resized image
    """

    height, width = image.shape[0], image.shape[1]

    # if the short side is the vertical one, then rescale the image width accordingly
    # otherwise the short side is the horizontal one, so rescale the image height accordingly
    if height < width:
        new_height = short_side_target_size
        new_width = width * new_height / height
    else:
        new_width = short_side_target_size
        new_height = height * new_width / width

    # make sure that new_height and new_width are a multiple of 32
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)

    # rescale and return the image
    return cv2.resize(image, (new_width, new_height))


def resize_image_from_large_side(image,
                                 large_side_target_size: int):
    """
    This utility method rescales a rectangular OpenCV image
    by resizing its large side to a passed target size
    (and rescaling the other side accordingly)

    @param: image: an image to resize
    @short_side_target_size: the size that we want the large side of the image to have,
                             after the image is resized

    @return: the resized image
    """

    height, width = image.shape[0], image.shape[1]

    # if the short side is the vertical one, then rescale the image width accordingly
    # otherwise the short side is the horizontal one, so rescale the image height accordingly
    if height > width:
        new_height = large_side_target_size
        new_width = new_height / height * width
    else:
        new_width = large_side_target_size
        new_height = new_width / width * height

    # make sure that new_height and new_width are a multiple of 32
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)

    # rescale and return the image
    return cv2.resize(image, (new_width, new_height))


def get_sub_image(rect, src):
    """
    This utility method uses the coordinates of a rectangle
    to extract and rotate the corresponding sub-image from a passed source image
    """

    # Get the rectangle coordinates: center, size, and rotation angle theta
    center, size, theta = rect

    # Convert the center and size coordinates to int
    center, size = tuple(map(int, center)), tuple(map(int, size))

    # Generate the rotation matrix that corresponds to the passed rectangle
    rotation_matrix = cv2.getRotationMatrix2D(center, theta, 1)

    # Rotate the source image applying the rotation matrix
    dst = cv2.warpAffine(src, rotation_matrix, src.shape[:2])

    # extract the rectangle from the rotated image using its size and center coordinates
    dst = np.float32(dst)
    out = cv2.getRectSubPix(dst, size, center)

    # if the image height is smaller than its width,
    # then rotate the extracted rectangle by 90 degrees
    # (because we are cropping images of text lines)
    h_out, w_out = out.shape
    if w_out < h_out:  # naive
        out = cv2.rotate(out, cv2.cv2.ROTATE_90_CLOCKWISE)

    return out
