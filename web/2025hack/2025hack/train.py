import tensorflow as tf
from tensorflow import keras
from keras import backend as k
from keras.layers import *
from keras.models import Model
from keras.optimizers import *
from keras.callbacks import *
import pickle
import gin
from tqdm import tqdm
from IPython.display import display
import gc
from pathlib import Path
import glob
import cv2
import matplotlib.pyplot as plt
import os
import random
import math
import numpy as np
import json
gin.enter_interactive_mode()

# Store the base directory (project root) before changing directories
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir("2025hack")
print(f"Working directory: {os.getcwd()}")

from modules import translator
# Use absolute paths for configuration files
gin.parse_config_file(os.path.join(base_dir, 'configs/translator_train.gin'))
gin.parse_config_file(os.path.join(base_dir, 'configs/utils.gin'))

skeleton_dir = "2025hack/data/skeletons"
checkpoint = None #"/home/yanng/2025hack/checkpoints/translator/2h20220915.h5"
target_epoch = 100
steps_per_epoch = 500

# online-hard-mining
n_hards = 50

h5_glosses = [p.stem for p in Path(skeleton_dir).glob("*.h5")]
LABELS = {}
for i, g in enumerate(h5_glosses):
    LABELS[g] = [i, g]
N_CLASSES = len(LABELS.keys())
print("N_CLASSES", N_CLASSES)
assert N_CLASSES > 1

with open("configs/labels.gin", "w") as f:
    dump_dict = json.dumps(LABELS, indent=0,separators=(',', ':'))
    f.writelines(f"LABELS = {dump_dict}\n")    
    f.writelines(f"N_CLASSES = {N_CLASSES}")

gin.parse_config_file('configs/translator_train.gin')
gin.parse_config_file('configs/utils.gin')

model = translator.get_model()
batch_size = model.outputs[0].shape[0]
n_feats = model.outputs[0].shape[1]
n_classes = model.outputs[1].shape[1]
print("batch_size:", batch_size)
print("n_feats:", n_feats)
print("n_classes:", n_classes)

if checkpoint is not None:
    model.load_weights(checkpoint)

train_generator = translator.DataGenerator(skeleton_dir)
assert len(train_generator.labels_dict) == N_CLASSES

initial_epoch = 0
hards = None


@tf.function
def custom_train_step(inputs, y_true):
    with tf.GradientTape() as tape:
        feats_pred, cls_pred = model(inputs, training=True)

        cls_loss = cce(y_true, cls_pred)

    grads = tape.gradient(cls_loss, model.trainable_weights)
    optimizer.apply_gradients(zip(grads, model.trainable_weights))
    acc_metrics.update_state(y_true, cls_pred)

    return cls_loss

optimizer = tf.optimizers.Adam(1e-3)

acc_metrics = tf.keras.metrics.SparseCategoricalAccuracy()
cce = tf.keras.losses.SparseCategoricalCrossentropy(
    reduction=tf.keras.losses.Reduction.NONE, from_logits=True)

for ep in range(initial_epoch, target_epoch):
    acc_metrics.reset_states()
    dh = display("", display_id=True)

    for step in range(steps_per_epoch):
        inputs, y_true = train_generator.__getitem__(0, hards)
        cls_loss = custom_train_step(inputs, y_true)
        cls_loss_np = cls_loss.numpy()

        # Online Hard Mining
        hards_b = np.argsort(cls_loss_np)[-n_hards:]
        hards = y_true[hards_b].squeeze().tolist()

        dh.update(f"epoch-{ep:02d} step-{step} cls_loss-{np.mean(cls_loss_np):.4f} acc-{acc_metrics.result().numpy():.4f}")

    if ep % 5 == 0:
        filepath=f"train_ckpts/{ep:02d}_{acc_metrics.result().numpy():.3f}.h5"
        model.save_weights(filepath)
    
# Create the save directory if it doesn't exist
os.makedirs("2025hack/checkpoints", exist_ok=True)
model.save("2025hack/checkpoints/trained.h5", save_format="h5")