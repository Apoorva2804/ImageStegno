import os, math, csv, argparse, warnings
from typing import Dict, List
import numpy as np, cv2
from skimage.metrics import structural_similarity as ssim
from steg_utils import image_ops, utils
warnings.filterwarnings("ignore")

# ---- metrics ----
def mse(x: np.ndarray, y: np.ndarray) -> float:
    d = x.astype(np.float64) - y.astype(np.float64)
    return float(np.mean(d ** 2))
def rmse(x: np.ndarray, y: np.ndarray) -> float:
    return math.sqrt(mse(x, y))
def psnr(x: np.ndarray, y: np.ndarray, max_val: float = 255.0) -> float:
    m = mse(x, y)
    return float("inf") if m == 0.0 else 20.0 * math.log10(max_val / math.sqrt(m))
def ncc(x: np.ndarray, y: np.ndarray) -> float:
    xv = x.astype(np.float64).ravel(); yv = y.astype(np.float64).ravel()
    xv -= xv.mean(); yv -= yv.mean()
    denom = np.linalg.norm(xv) * np.linalg.norm(yv)
    return float((xv @ yv) / denom) if denom != 0.0 else 0.0
def ssim_index(x: np.ndarray, y: np.ndarray) -> float:
    return float(ssim(x, y, channel_axis=-1, data_range=255))

# ---- helpers ----
def _resize_rgb(arr: np.ndarray, side: int) -> np.ndarray:
    return cv2.resize(arr, (side, side), interpolation=cv2.INTER_AREA)
def _fit_payload(payload: bytes, capacity_bits: int, header_bits: int = 32) -> bytes:
    max_bytes = max((capacity_bits - header_bits) // 8, 0)
    return payload[:max_bytes]
def _embed_rgb(cover_rgb: np.ndarray, payload: bytes, key: str, bpp: int) -> np.ndarray:
    proc = image_ops.flip_transpose(cover_rgb)
    r, g, b = image_ops.split_rgb(proc)
    blocks, split_idx = image_ops.split_blue_blocks(b)
    perm = utils.generate_perm_from_key(key)
    shuffled = [blocks[p] for p in perm]
    shuffled_blue = image_ops.combine_blue_blocks(shuffled, b.shape, split_idx)
    header = len(payload).to_bytes(4, "big")
    stego_shuf = utils.embed_payload_in_channel(shuffled_blue, header + payload, bits_per_pixel=bpp)
    stego_blue = utils.unshuffle_to_visual_with_indices(stego_shuf, perm, split_idx)
    stego_proc = image_ops.merge_rgb(r, g, stego_blue)
    return image_ops.inv_flip_transpose(stego_proc)
def _load_payload(enc_file: str) -> bytes:
    with open(enc_file, "rb") as f:
        return f.read()

# ---- evaluation ----
def evaluate_per_size(cover_path: str, payload: bytes, key: str, bpp: int, side: int,
                      out_dir: str = "output") -> Dict[str, float]:
    cover_rgb = image_ops.load_image(cover_path)   # RGB
    cover_resized = _resize_rgb(cover_rgb, side)
    stego = _embed_rgb(cover_resized, payload, key, bpp)
    os.makedirs(out_dir, exist_ok=True)
    image_ops.save_image(stego, os.path.join(out_dir, f"stego_{side}.png"))
    return {
        "MSE": mse(cover_resized, stego),
        "RMSE": rmse(cover_resized, stego),
        "PSNR": psnr(cover_resized, stego),
        "NCC": ncc(cover_resized, stego),
        "SSIM": ssim_index(cover_resized, stego),
    }

def run_single_pair(cover_path: str, enc_file: str, key: str, bpp: int,
                    dims: List[int]) -> Dict[int, Dict[str, float]]:
    payload_full = _load_payload(enc_file)
    min_side = min(dims)
    min_capacity_bits = (min_side * min_side) * bpp
    payload = _fit_payload(payload_full, min_capacity_bits)   # fits all sizes
    results = {}
    for d in dims:
        results[d] = evaluate_per_size(cover_path, payload, key, bpp, d)
    return results

# ---- reporting ----
def print_table(results: Dict[int, Dict[str, float]]) -> None:
    print("Dimension |    MSE    |   RMSE   |  PSNR(dB) |    NCC    |    SSIM")
    print("-" * 70)
    for d in sorted(results):
        r = results[d]
        ps = f"{r['PSNR']:.2f}" if math.isfinite(r["PSNR"]) else "inf"
        print(f"{d}x{d}    | {r['MSE']:.6f} | {r['RMSE']:.6f} | {ps:>8} | {r['NCC']:.6f} | {r['SSIM']:.6f}")

def save_csv(results: Dict[int, Dict[str, float]], out_csv: str) -> None:
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Dimension", "MSE", "RMSE", "PSNR(dB)", "NCC", "SSIM"])
        for d in sorted(results):
            r = results[d]
            w.writerow([f"{d}x{d}", f"{r['MSE']:.6f}", f"{r['RMSE']:.6f}",
                        f"{r['PSNR']:.6f}" if math.isfinite(r["PSNR"]) else "inf",
                        f"{r['NCC']:.6f}", f"{r['SSIM']:.6f}"])

# ---- CLI ----
def main():
    ap = argparse.ArgumentParser(description="Re-embed per dimension and compute metrics")
    ap.add_argument("--cover", required=True)
    ap.add_argument("--enc", default="output/encrypted.bin")
    ap.add_argument("--key", required=True)
    ap.add_argument("--bpp", type=int, default=1, choices=[1,2,3,4])
    ap.add_argument("--dims", nargs="+", type=int, default=[128, 256, 512, 1024])
    ap.add_argument("--out_csv", default="results/metrics_single_pair.csv")
    args = ap.parse_args()
    results = run_single_pair(args.cover, args.enc, args.key, args.bpp, args.dims)
    print_table(results); save_csv(results, args.out_csv)
    print("\nPSNR by dimension:")
    for d in sorted(results):
        val = results[d]["PSNR"]
        print(f"D-{d} = {val:.2f} dB" if math.isfinite(val) else f"D-{d} = inf dB")

if __name__ == "__main__":
    main()

#python metrics.py --cover input/cover.png --stego output/stego.png --dims 128 256 512 1024
