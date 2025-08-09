import numpy as np
import cv2

def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Image not found at path: " + path)
    return img

def split_rgb(img):
    return cv2.split(img)

def flip_planes(r, g, b):
    r_flipped = cv2.flip(r, 1)   # horizontal flip
    g_flipped = cv2.flip(g, 0)   # vertical flip
    b_flipped = cv2.transpose(b)  # diagonal flip
    return r_flipped, g_flipped, b_flipped

def merge_rgb(r, g, b):
    return cv2.merge((r, g, b))
