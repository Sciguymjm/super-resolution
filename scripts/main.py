import tensorflow as tf
import numpy as np
import argparse

LEARNING_RATE = 1e-4
BATCH_SIZE = 1
MAX_STEPS = 30e3

def train(args, global_step):
    pass

def main(args):
    global_step = tf.Variable(0, trainable=False)
    train(args, global_step)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--train", action="store_true", help="Train a new model")
    parser.add_argument("-lr", type=float, default=LEARNING_RATE, help="Learning rate")
    parser.add_argument("-max", type=int, default=MAX_STEPS, help="Max number of steps to take")
    parser.add_argument("-check", type=str, default=".", help="Checkpoint directory")
    args = parser.parse_args()
    main(args)
