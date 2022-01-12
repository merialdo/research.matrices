# -*- coding: utf-8 -*-
# @Time    : 2020/6/16 23:46
# @Author  : zonas.wang
# @Email   : zonas.wang@gmail.com
# @File    : model.py
import tensorflow as tf
from tensorflow import keras as K
from tensorflow.keras import layers as KL

# Metriche positive e dei mini script che funzionino



#from text_detector.losses import db_loss

from losses import db_loss


class BatchNormalization(KL.BatchNormalization):
    """
    Identical to KL.BatchNormalization, but adds the option to freeze parameters.
    """
    def __init__(self, freeze, *args, **kwargs):
        self.freeze = freeze
        super(BatchNormalization, self).__init__(*args, **kwargs)

        # set to non-trainable if freeze is true
        self.trainable = not self.freeze

    def call(self, *args, **kwargs):
        # Force test mode if frozen, otherwise use default behaviour (i.e., training=None).
        if self.freeze:
            kwargs['training'] = False
        return super(BatchNormalization, self).call(*args, **kwargs)

    def get_config(self):
        config = super(BatchNormalization, self).get_config()
        config.update({'freeze': self.freeze})
        return config


parameters = {
    "kernel_initializer": "he_normal"
}


class ResNet(tf.keras.Model):
    """
    Constructs a `keras.models.Model` object using the given block count.
    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)
    :param blocks: the network’s residual architecture
    :param block: a residual block (e.g. an instance of `keras_resnet.blocks.basic_2d`)
    :param include_top: if true, includes classification layers
    :param classes: number of classes to classify (include_top must be true)
    :param freeze_bn: if true, freezes BatchNormalization layers (ie. no updates are done in these layers)
    :param numerical_names: list of bool, same size as blocks, used to indicate whether names of layers should include numbers or letters
    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)
    Usage:
    """
    def __init__(
        self,
        inputs,
        blocks,
        block,
        include_top=True,
        classes=1000,
        freeze_bn=True,
        numerical_names=None,
        *args,
        **kwargs
    ):
        if K.backend.image_data_format() == "channels_last":
            axis = 3
        else:
            axis = 1

        if numerical_names is None:
            numerical_names = [True] * len(blocks)

        x = KL.Conv2D(64, (7, 7), strides=(2, 2), use_bias=False, name="conv1", padding="same")(inputs)
        x = BatchNormalization(axis=axis, epsilon=1e-5, freeze=freeze_bn, name="bn_conv1")(x)
        x = KL.Activation("relu", name="conv1_relu")(x)
        x = KL.MaxPooling2D((3, 3), strides=(2, 2), padding="same", name="pool1")(x)

        features = 64

        outputs = []

        for stage_id, iterations in enumerate(blocks):
            for block_id in range(iterations):
                x = block(
                    features,
                    stage_id,
                    block_id,
                    numerical_name=(block_id > 0 and numerical_names[stage_id]),
                    freeze_bn=freeze_bn
                )(x)

            features *= 2

            outputs.append(x)

        if include_top:
            assert classes > 0

            x = KL.GlobalAveragePooling2D(name="pool5")(x)
            x = KL.Dense(classes, activation="softmax", name="fc1000")(x)

            super(ResNet, self).__init__(inputs=inputs, outputs=x, *args, **kwargs)
        else:
            # Else output each stages features
            super(ResNet, self).__init__(inputs=inputs, outputs=outputs, *args, **kwargs)

def resnet_bottleneck(
    filters,
    stage=0,
    block=0,
    kernel_size=3,
    numerical_name=False,
    stride=None,
    freeze_bn=False
):
    """
    A two-dimensional bottleneck block.
    :param filters: the output’s feature space
    :param stage: int representing the stage of this block (starting from 0)
    :param block: int representing this block (starting from 0)
    :param kernel_size: size of the kernel
    :param numerical_name: if true, uses numbers to represent blocks instead of chars (ResNet{101, 152, 200})
    :param stride: int representing the stride used in the shortcut and the first conv layer, default derives stride from block id
    :param freeze_bn: if true, freezes BatchNormalization layers (ie. no updates are done in these layers)
    Usage:
    """
    if stride is None:
        if block != 0 or stage == 0:
            stride = 1
        else:
            stride = 2

    if K.backend.image_data_format() == "channels_last":
        axis = 3
    else:
        axis = 1

    if block > 0 and numerical_name:
        block_char = "b{}".format(block)
    else:
        block_char = chr(ord('a') + block)

    stage_char = str(stage + 2)

    def f(x):
        y = KL.Conv2D(filters, (1, 1), strides=stride, use_bias=False, name="res{}{}_branch2a".format(stage_char, block_char), **parameters)(x)

        y = BatchNormalization(axis=axis, epsilon=1e-5, freeze=freeze_bn, name="bn{}{}_branch2a".format(stage_char, block_char))(y)

        y = KL.Activation("relu", name="res{}{}_branch2a_relu".format(stage_char, block_char))(y)

        y = KL.ZeroPadding2D(padding=1, name="padding{}{}_branch2b".format(stage_char, block_char))(y)

        y = KL.Conv2D(filters, kernel_size, use_bias=False, name="res{}{}_branch2b".format(stage_char, block_char), **parameters)(y)

        y = BatchNormalization(axis=axis, epsilon=1e-5, freeze=freeze_bn, name="bn{}{}_branch2b".format(stage_char, block_char))(y)

        y = KL.Activation("relu", name="res{}{}_branch2b_relu".format(stage_char, block_char))(y)

        y = KL.Conv2D(filters * 4, (1, 1), use_bias=False, name="res{}{}_branch2c".format(stage_char, block_char), **parameters)(y)

        y = BatchNormalization(axis=axis, epsilon=1e-5, freeze=freeze_bn, name="bn{}{}_branch2c".format(stage_char, block_char))(y)

        if block == 0:
            shortcut = KL.Conv2D(filters * 4, (1, 1), strides=stride, use_bias=False, name="res{}{}_branch1".format(stage_char, block_char), **parameters)(x)

            shortcut = BatchNormalization(axis=axis, epsilon=1e-5, freeze=freeze_bn, name="bn{}{}_branch1".format(stage_char, block_char))(shortcut)
        else:
            shortcut = x

        y = KL.Add(name="res{}{}".format(stage_char, block_char))([y, shortcut])

        y = KL.Activation("relu", name="res{}{}_relu".format(stage_char, block_char))(y)

        return y

    return f


class ResNet50(ResNet):
    """
    Constructs a `keras.models.Model` according to the ResNet50 specifications.
    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)
    :param blocks: the network’s residual architecture
    :param include_top: if true, includes classification layers
    :param classes: number of classes to classify (include_top must be true)
    :param freeze_bn: if true, freezes BatchNormalization layers (ie. no updates are done in these layers)
    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)
    Usage:
    """
    def __init__(self, inputs, blocks=None, include_top=True, classes=1000, freeze_bn=False, *args, **kwargs):
        if blocks is None:
            blocks = [3, 4, 6, 3]

        numerical_names = [False, False, False, False]

        super(ResNet50, self).__init__(
            inputs,
            blocks,
            numerical_names=numerical_names,
            block=resnet_bottleneck,
            include_top=include_top,
            classes=classes,
            freeze_bn=freeze_bn,
            *args,
            **kwargs
        )



def DBNet(cfg, k=50, model='training'):
    assert model in ['training', 'inference'], 'error'

    input_image = KL.Input(shape=[None, None, 3], name='input_image')

    backbone = ResNet50(inputs=input_image, include_top=False, freeze_bn=True)
    C2, C3, C4, C5 = backbone.outputs

    # in2
    in2 = KL.Conv2D(256, (1, 1), padding='same', kernel_initializer='he_normal', name='in2')(C2)
    in2 = KL.BatchNormalization()(in2)
    in2 = KL.ReLU()(in2)
    # in3
    in3 = KL.Conv2D(256, (1, 1), padding='same', kernel_initializer='he_normal', name='in3')(C3)
    in3 = KL.BatchNormalization()(in3)
    in3 = KL.ReLU()(in3)
    # in4
    in4 = KL.Conv2D(256, (1, 1), padding='same', kernel_initializer='he_normal', name='in4')(C4)
    in4 = KL.BatchNormalization()(in4)
    in4 = KL.ReLU()(in4)
    # in5
    in5 = KL.Conv2D(256, (1, 1), padding='same', kernel_initializer='he_normal', name='in5')(C5)
    in5 = KL.BatchNormalization()(in5)
    in5 = KL.ReLU()(in5)

    # P5
    P5 = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal')(in5)
    P5 = KL.BatchNormalization()(P5)
    P5 = KL.ReLU()(P5)
    P5 = KL.UpSampling2D(size=(8, 8))(P5)
    # P4
    out4 = KL.Add()([in4, KL.UpSampling2D(size=(2, 2))(in5)])
    P4 = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal')(out4)
    P4 = KL.BatchNormalization()(P4)
    P4 = KL.ReLU()(P4)
    P4 = KL.UpSampling2D(size=(4, 4))(P4)
    # P3
    out3 = KL.Add()([in3, KL.UpSampling2D(size=(2, 2))(out4)])
    P3 = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal')(out3)
    P3 = KL.BatchNormalization()(P3)
    P3 = KL.ReLU()(P3)
    P3 = KL.UpSampling2D(size=(2, 2))(P3)
    # P2
    out2 = KL.Add()([in2, KL.UpSampling2D(size=(2, 2))(out3)])
    P2 = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal')(out2)
    P2 = KL.BatchNormalization()(P2)
    P2 = KL.ReLU()(P2)

    fuse = KL.Concatenate()([P2, P3, P4, P5])

    # binarize map
    p = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal', use_bias=False)(fuse)
    p = KL.BatchNormalization()(p)
    p = KL.ReLU()(p)
    p = KL.Conv2DTranspose(64, (2, 2), strides=(2, 2), kernel_initializer='he_normal', use_bias=False)(p)
    p = KL.BatchNormalization()(p)
    p = KL.ReLU()(p)
    binarize_map  = KL.Conv2DTranspose(1, (2, 2), strides=(2, 2), kernel_initializer='he_normal',
                                       activation='sigmoid', name='binarize_map')(p)

    # threshold map
    t = KL.Conv2D(64, (3, 3), padding='same', kernel_initializer='he_normal', use_bias=False)(fuse)
    t = KL.BatchNormalization()(t)
    t = KL.ReLU()(t)
    t = KL.Conv2DTranspose(64, (2, 2), strides=(2, 2), kernel_initializer='he_normal', use_bias=False)(t)
    t = KL.BatchNormalization()(t)
    t = KL.ReLU()(t)
    threshold_map = KL.Conv2DTranspose(1, (2, 2), strides=(2, 2), kernel_initializer='he_normal',
                                        activation='sigmoid', name='threshold_map')(t)

    # thresh binary map
    thresh_binary = KL.Lambda(lambda x: 1 / (1 + tf.exp(-k * (x[0] - x[1]))))([binarize_map, threshold_map])

    if model == 'training':
        input_gt = KL.Input(shape=[cfg.IMAGE_SIZE, cfg.IMAGE_SIZE], name='input_gt')
        input_mask = KL.Input(shape=[cfg.IMAGE_SIZE, cfg.IMAGE_SIZE], name='input_mask')
        input_thresh = KL.Input(shape=[cfg.IMAGE_SIZE, cfg.IMAGE_SIZE], name='input_thresh')
        input_thresh_mask = KL.Input(shape=[cfg.IMAGE_SIZE, cfg.IMAGE_SIZE], name='input_thresh_mask')

        loss_layer = KL.Lambda(db_loss, name='db_loss')(
            [input_gt, input_mask, input_thresh, input_thresh_mask, binarize_map, thresh_binary, threshold_map])

        db_model = K.Model(inputs=[input_image, input_gt, input_mask, input_thresh, input_thresh_mask],
                           outputs=[loss_layer])

        loss_names = ["db_loss"]
        for layer_name in loss_names:
            layer = db_model.get_layer(layer_name)
            db_model.add_loss(layer.output)
            # db_model.add_metric(layer.output, name=layer_name, aggregation="mean")
    else:
        db_model = K.Model(inputs=input_image,
                           outputs=binarize_map)
        """
        db_model = K.Model(inputs=input_image,
                           outputs=thresh_binary)
        """
    return db_model


if __name__ == '__main__':
    from config import DBConfig
    cfg = DBConfig()
    model = DBNet(cfg, model='inference')
    model.summary()
