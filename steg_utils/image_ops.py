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
    Per the paper: first horizontal flip, then transpose.
    That is: FT = transpose(flip(image, horizontal))
    """
    # horizontal flip (mirror left-right)
    flipped = np.flip(img_arr, axis=1)
    # transpose rows <-> cols
    img_t = np.transpose(flipped, (1, 0, 2))
    return img_t

def inv_flip_transpose(img_arr: np.ndarray) -> np.ndarray:
    """
    Inverse of flip_transpose:
    If forward was transpose(flip(img)), inverse is flip(transpose(img))
    """
    transposed = np.transpose(img_arr, (1, 0, 2))
    inv = np.flip(transposed, axis=1)
    return inv

def split_rgb(img_arr: np.ndarray):
    r = img_arr[:, :, 0].copy()
    g = img_arr[:, :, 1].copy()
    b = img_arr[:, :, 2].copy()
    return r, g, b

def merge_rgb(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    arr = np.stack([r, g, b], axis=2).astype("uint8")
    return arr

def split_blue_blocks(blue: np.ndarray):
    """
    Splits blue channel into 4 nearly-equal quadrants:
    BC1: top-left, BC2: top-right, BC3: bottom-left, BC4: bottom-right
    Handles odd dimensions safely by using ceil for the bottom/right blocks.
    Returns list [BC1, BC2, BC3, BC4] and the split indices (mh, mw) for recombination.
    """
    h, w = blue.shape
    mh = h // 2
    mw = w // 2
    # top-left
    bc1 = blue[0:mh, 0:mw].copy()
    # top-right
    bc2 = blue[0:mh, mw:w].copy()
    # bottom-left
    bc3 = blue[mh:h, 0:mw].copy()
    # bottom-right
    bc4 = blue[mh:h, mw:w].copy()
    return [bc1, bc2, bc3, bc4], (mh, mw)

def combine_blue_blocks(blocks: list, shape: tuple, split_indices: tuple):
    """
    Recombine four blocks into a blue channel of given shape.
    Expects blocks in order [BC1, BC2, BC3, BC4].
    split_indices must be the (mh, mw) returned from split_blue_blocks to handle odd sizes.
    """
    h, w = shape
    mh, mw = split_indices
    out = np.zeros((h, w), dtype=np.uint8)
    out[0:mh, 0:mw] = blocks[0]
    out[0:mh, mw:w] = blocks[1]
    out[mh:h, 0:mw] = blocks[2]
    out[mh:h, mw:w] = blocks[3]
    return out
