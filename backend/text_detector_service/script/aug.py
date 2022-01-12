# Copyright (C) 2021, Mindee.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

import random
import tensorflow as tf
from typing import List, Any, Tuple, Callable, Optional


#__all__ = ["invert_colors"]


def invert_colors(img: tf.Tensor, min_val: Optional[float] = 0.6) -> tf.Tensor:
    out = tf.image.rgb_to_grayscale(img)  # Convert to gray
    # Random RGB shift
    shift_shape = [img.shape[0], 1, 1, 3] if img.ndim == 4 else [1, 1, 3]
    rgb_shift = tf.random.uniform(shape=shift_shape, minval=min_val, maxval=1)
    # Inverse the color
    if out.dtype == tf.uint8:
        out = tf.cast(tf.cast(out, dtype=tf.float32) * rgb_shift, dtype=tf.uint8)
    else:
        out *= rgb_shift
    # Inverse the color
    out = 255 - out if out.dtype == tf.uint8 else 1 - out
    return out


__all__ = ['Compose', 'Resize', 'Normalize', 'LambdaTransformation', 'ToGray', 'ColorInversion',
           'RandomBrightness', 'RandomContrast', 'RandomSaturation', 'RandomHue', 'RandomGamma', 'RandomJpegQuality',
           'OneOf', 'RandomApply']


#__all__ = ['NestedObject']


def _addindent(s_, num_spaces):
    s = s_.split('\n')
    # don't do anything for single-line stuff
    if len(s) == 1:
        return s_
    first = s.pop(0)
    s = [(num_spaces * ' ') + line for line in s]
    s = '\n'.join(s)
    s = first + '\n' + s
    return s


class NestedObject:
    def extra_repr(self) -> str:
        return ''

    def __repr__(self):
        # We treat the extra repr like the sub-object, one item per line
        extra_lines = []
        extra_repr = self.extra_repr()
        # empty string will be split into list ['']
        if extra_repr:
            extra_lines = extra_repr.split('\n')
        child_lines = []
        if hasattr(self, '_children_names'):
            for key in self._children_names:
                child = getattr(self, key)
                if isinstance(child, list) and len(child) > 0:
                    child_str = ",\n".join([repr(subchild) for subchild in child])
                    if len(child) > 1:
                        child_str = _addindent(f"\n{child_str},", 2) + '\n'
                    child_str = f"[{child_str}]"
                else:
                    child_str = repr(child)
                child_str = _addindent(child_str, 2)
                child_lines.append('(' + key + '): ' + child_str)
        lines = extra_lines + child_lines

        main_str = self.__class__.__name__ + '('
        if lines:
            # simple one-liner info, which most builtin Modules will use
            if len(extra_lines) == 1 and not child_lines:
                main_str += extra_lines[0]
            else:
                main_str += '\n  ' + '\n  '.join(lines) + '\n'

        main_str += ')'
        return main_str


class Compose(NestedObject):
    """Implements a wrapper that will apply transformations sequentially
    Example::
        from doctr.transforms import Compose, Resize
        import tensorflow as tf
        transfos = Compose([Resize((32, 32))])
        out = transfos(tf.random.uniform(shape=[64, 64, 3], minval=0, maxval=1))
    Args:
        transforms: list of transformation modules
    """

    _children_names: List[str] = ['transforms']

    def __init__(self, transforms: List[NestedObject]) -> None:
        self.transforms = transforms

    def __call__(self, x: Any) -> Any:
        for t in self.transforms:
            x = t(x)

        return x


class Resize(NestedObject):
    """Resizes a tensor to a target size
    Example::
        from doctr.transforms import Resize
        import tensorflow as tf
        transfo = Resize((32, 32))
        out = transfo(tf.random.uniform(shape=[64, 64, 3], minval=0, maxval=1))
    Args:
        output_size: expected output size
        method: interpolation method
        preserve_aspect_ratio: if `True`, preserve aspect ratio and pad the rest with zeros
        symmetric_pad: if `True` while preserving aspect ratio, the padding will be done symmetrically
    """
    def __init__(
        self,
        output_size: Tuple[int, int],
        method: str = 'bilinear',
        preserve_aspect_ratio: bool = False,
        symmetric_pad: bool = False,
    ) -> None:
        self.output_size = output_size
        self.method = method
        self.preserve_aspect_ratio = preserve_aspect_ratio
        self.symmetric_pad = symmetric_pad

    def extra_repr(self) -> str:
        _repr = f"output_size={self.output_size}, method='{self.method}'"
        if self.preserve_aspect_ratio:
            _repr += f", preserve_aspect_ratio={self.preserve_aspect_ratio}, symmetric_pad={self.symmetric_pad}"
        return _repr

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        img = tf.image.resize(img, self.output_size, self.method, self.preserve_aspect_ratio)
        if self.preserve_aspect_ratio:
            # pad width
            if not self.symmetric_pad:
                offset = (0, 0)
            elif self.output_size[0] == img.shape[0]:
                offset = (0, int((self.output_size[1] - img.shape[1]) / 2))
            else:
                offset = (int((self.output_size[0] - img.shape[0]) / 2), 0)
            img = tf.image.pad_to_bounding_box(img, *offset, *self.output_size)
        return img


class Normalize(NestedObject):
    """Normalize a tensor to a Gaussian distribution for each channel
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        mean: average value per channel
        std: standard deviation per channel
    """
    def __init__(self, mean: Tuple[float, float, float], std: Tuple[float, float, float]) -> None:
        self.mean = tf.constant(mean, dtype=tf.float32)
        self.std = tf.constant(std, dtype=tf.float32)

    def extra_repr(self) -> str:
        return f"mean={self.mean.numpy().tolist()}, std={self.std.numpy().tolist()}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        img -= self.mean
        img /= self.std
        return img


class LambdaTransformation(NestedObject):
    """Normalize a tensor to a Gaussian distribution for each channel
    Example::
        from doctr.transforms import LambdaTransformation
        import tensorflow as tf
        transfo = LambdaTransformation(lambda x: x/ 255.)
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        fn: the function to be applied to the input tensor
    """
    def __init__(self, fn: Callable[[tf.Tensor], tf.Tensor]) -> None:
        self.fn = fn

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return self.fn(img)


class ToGray(NestedObject):
    """Convert a RGB tensor (batch of images or image) to a 3-channels grayscale tensor
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = ToGray()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    """
    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.rgb_to_grayscale(img)


class ColorInversion(NestedObject):
    """Applies the following tranformation to a tensor (image or batch of images):
    convert to grayscale, colorize (shift 0-values randomly), and then invert colors
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = ColorInversion(min_val=0.6)
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        min_val: range [min_val, 1] to colorize RGB pixels
    """
    def __init__(self, min_val: float = 0.6) -> None:
        self.min_val = min_val

    def extra_repr(self) -> str:
        return f"min_val={self.min_val}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return invert_colors(img, self.min_val)


class RandomBrightness(NestedObject):
    """Randomly adjust brightness of a tensor (batch of images or image) by adding a delta
    to all pixels
    Example:
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Brightness()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        max_delta: offset to add to each pixel is randomly picked in [-max_delta, max_delta]
        p: probability to apply transformation
    """
    def __init__(self, max_delta: float = 0.3) -> None:
        self.max_delta = max_delta

    def extra_repr(self) -> str:
        return f"max_delta={self.max_delta}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.random_brightness(img, max_delta=self.max_delta)


class RandomContrast(NestedObject):
    """Randomly adjust contrast of a tensor (batch of images or image) by adjusting
    each pixel: (img - mean) * contrast_factor + mean.
    Example:
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Contrast()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        delta: multiplicative factor is picked in [1-delta, 1+delta] (reduce contrast if factor<1)
    """
    def __init__(self, delta: float = .3) -> None:
        self.delta = delta

    def extra_repr(self) -> str:
        return f"delta={self.delta}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.random_contrast(img, lower=1 - self.delta, upper=1 / (1 - self.delta))


class RandomSaturation(NestedObject):
    """Randomly adjust saturation of a tensor (batch of images or image) by converting to HSV and
    increasing saturation by a factor.
    Example:
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Saturation()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        delta: multiplicative factor is picked in [1-delta, 1+delta] (reduce saturation if factor<1)
    """
    def __init__(self, delta: float = .5) -> None:
        self.delta = delta

    def extra_repr(self) -> str:
        return f"delta={self.delta}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.random_saturation(img, lower=1 - self.delta, upper=1 + self.delta)


class RandomHue(NestedObject):
    """Randomly adjust hue of a tensor (batch of images or image) by converting to HSV and adding a delta
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Hue()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        max_delta: offset to add to each pixel is randomly picked in [-max_delta, max_delta]
    """
    def __init__(self, max_delta: float = 0.3) -> None:
        self.max_delta = max_delta

    def extra_repr(self) -> str:
        return f"max_delta={self.max_delta}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.random_hue(img, max_delta=self.max_delta)


class RandomGamma(NestedObject):
    """randomly performs gamma correction for a tensor (batch of images or image)
    Example:
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = Gamma()
        out = transfo(tf.random.uniform(shape=[8, 64, 64, 3], minval=0, maxval=1))
    Args:
        min_gamma: non-negative real number, lower bound for gamma param
        max_gamma: non-negative real number, upper bound for gamma
        min_gain: lower bound for constant multiplier
        max_gain: upper bound for constant multiplier
    """
    def __init__(
        self,
        min_gamma: float = 0.5,
        max_gamma: float = 1.5,
        min_gain: float = 0.8,
        max_gain: float = 1.2,
    ) -> None:
        self.min_gamma = min_gamma
        self.max_gamma = max_gamma
        self.min_gain = min_gain
        self.max_gain = max_gain

    def extra_repr(self) -> str:
        return f"""gamma_range=({self.min_gamma}, {self.max_gamma}),
                 gain_range=({self.min_gain}, {self.max_gain})"""

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        gamma = random.uniform(self.min_gamma, self.max_gamma)
        gain = random.uniform(self.min_gain, self.max_gain)
        return tf.image.adjust_gamma(img, gamma=gamma, gain=gain)


class RandomJpegQuality(NestedObject):
    """Randomly adjust jpeg quality of a 3 dimensional RGB image
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = JpegQuality()
        out = transfo(tf.random.uniform(shape=[64, 64, 3], minval=0, maxval=1))
    Args:
        min_quality: int between [0, 100]
        max_quality: int between [0, 100]
    """
    def __init__(self, min_quality: int = 60, max_quality: int = 100) -> None:
        self.min_quality = min_quality
        self.max_quality = max_quality

    def extra_repr(self) -> str:
        return f"min_quality={self.min_quality}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        return tf.image.random_jpeg_quality(
            img, min_jpeg_quality=self.min_quality, max_jpeg_quality=self.max_quality
        )


class OneOf(NestedObject):
    """Randomly apply one of the input transformations
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = OneOf([JpegQuality(), Gamma()])
        out = transfo(tf.random.uniform(shape=[64, 64, 3], minval=0, maxval=1))
    Args:
        transforms: list of transformations, one only will be picked
    """

    _children_names: List[str] = ['transforms']

    def __init__(self, transforms: List[NestedObject]) -> None:
        self.transforms = transforms

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        # Pick transformation
        transfo = self.transforms[int(random.random() * len(self.transforms))]
        # Apply
        return transfo(img)


class RandomApply(NestedObject):
    """Apply with a probability p the input transformation
    Example::
        from doctr.transforms import Normalize
        import tensorflow as tf
        transfo = RandomApply(Gamma(), p=.5)
        out = transfo(tf.random.uniform(shape=[64, 64, 3], minval=0, maxval=1))
    Args:
        transform: transformation to apply
        p: probability to apply
    """
    def __init__(self, transform: NestedObject, p: float = .5) -> None:
        self.transform = transform
        self.p = p

    def extra_repr(self) -> str:
        return f"transform={self.transform}, p={self.p}"

    def __call__(self, img: tf.Tensor) -> tf.Tensor:
        if random.random() < self.p:
            return self.transform(img)
        return img