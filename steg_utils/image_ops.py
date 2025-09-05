from PIL import Image
import numpy as np

def load_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img, dtype=np.uint8)

def save_image(arr: np.ndarray, path: str):
    Image.fromarray(arr.astype("uint8")).save(path)

def flip_transpose(img_arr: np.ndarray) -> np.ndarray:
    """
    Apply the internal transform used by the algorithm:
    - transpose (swap axes)
    - horizontal flip
    """
    img_t = np.transpose(img_arr, (1, 0, 2))
    img_t = np.flip(img_t, axis=1)
    return img_t

def inv_flip_transpose(img_arr: np.ndarray) -> np.ndarray:
    """
    Inverse of flip_transpose (used before saving stego back to original orientation).
    """
    img_t = np.flip(img_arr, axis=1)
    img_t = np.transpose(img_t, (1, 0, 2))
    return img_t

def split_rgb(img_arr: np.ndarray):
    r = img_arr[:, :, 0].copy()
    g = img_arr[:, :, 1].copy()
    b = img_arr[:, :, 2].copy()
    return r, g, b

def merge_rgb(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.stack([r, g, b], axis=2).astype("uint8")

def split_blue_blocks(blue: np.ndarray):
    """
    Splits blue channel into 4 nearly-equal quadrants:
    BC1: top-left, BC2: top-right, BC3: bottom-left, BC4: bottom-right
    Returns list [BC1, BC2, BC3, BC4]
    """
    h, w = blue.shape
    mh, mw = h // 2, w // 2
    bc1 = blue[0:mh, 0:mw].copy()
    bc2 = blue[0:mh, mw:w].copy()
    bc3 = blue[mh:h, 0:mw].copy()
    bc4 = blue[mh:h, mw:w].copy()
    return [bc1, bc2, bc3, bc4]

def combine_blue_blocks(blocks: list, shape: tuple):
    h, w = shape
    mh, mw = h // 2, w // 2
    out = np.zeros((h, w), dtype=np.uint8)
    out[0:mh, 0:mw] = blocks[0]
    out[0:mh, mw:w] = blocks[1]
    out[mh:h, 0:mw] = blocks[2]
    out[mh:h, mw:w] = blocks[3]
    return out
