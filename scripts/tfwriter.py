import glob

import numpy as np
import rasterio
import tensorflow as tf


def _float_feature(value):
    return tf.train.Feature(int64_list=tf.train.FloatList(value=[value.astype(float).tolist()]))


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def write_group_to_tfrecord(filename, files):

    writer = tf.python_io.TFRecordWriter(filename)

    for i, o in files:
        inp = rasterio.open(i).read(1)
        out = rasterio.open(o).read(1)
        feature = {'train/label': _bytes_feature(inp.tobytes()),
                   'train/image': _bytes_feature(out.tobytes())}
        example = tf.train.Example(features=tf.train.Features(feature=feature))

        # Serialize to string and write on the file
        writer.write(example.SerializeToString())
    writer.close()


inputs = np.array(sorted(glob.glob('../data/tiles/273/g_*')))
outputs = np.array(sorted(glob.glob('../data/tiles/273/m_*')))

msk = np.random.random(len(inputs)) < 0.8
train_inputs, test_inputs = inputs[msk], inputs[~msk]
train_outputs, test_outputs = outputs[msk], outputs[~msk]

valmsk = np.random.random(len(test_inputs)) > 0.5
test_inputs, val_inputs = test_inputs[valmsk], test_inputs[~valmsk]
test_outputs, val_outputs = test_outputs[valmsk], test_outputs[~valmsk]

write_group_to_tfrecord('train.tfrecords', zip(train_inputs, train_outputs))
write_group_to_tfrecord('test.tfrecords', zip(test_inputs, test_outputs))
write_group_to_tfrecord('val.tfrecords', zip(val_inputs, val_outputs))
