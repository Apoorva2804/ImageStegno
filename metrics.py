import os, math, csv, argparse, warnings
from typing import Dict, Tuple, List
import cv2, numpy as np
from skimage.metrics import structural_similarity as ssim
warnings.filterwarnings("ignore")

# -------- I/O --------
def load_image_bgr(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img  # [web:14]

def ensure_same_size(a: np.ndarray, b: np.ndarray, size: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    w, h = size  # (width, height) for OpenCV
    a_h, a_w = a.shape, a.shape[2]
    b_h, b_w = b.shape, b.shape[2]
    a_down = (a_w >= w) and (a_h >= h)
    b_down = (b_w >= w) and (b_h >= h)
    interp_a = cv2.INTER_AREA if a_down else cv2.INTER_LINEAR
    interp_b = cv2.INTER_AREA if b_down else cv2.INTER_LINEAR
    return (cv2.resize(a, (w, h), interpolation=interp_a),
            cv2.resize(b, (w, h), interpolation=interp_b))  # [3][4]

# -------- Metrics --------
def mse(x: np.ndarray, y: np.ndarray) -> float:
    d = x.astype(np.float64) - y.astype(np.float64)
    return float(np.mean(d ** 2))  # [4]

def rmse(x: np.ndarray, y: np.ndarray) -> float:
    return math.sqrt(mse(x, y))  # [4]

def psnr(x: np.ndarray, y: np.ndarray, max_val: float = 255.0) -> float:
    m = mse(x, y)
    return float("inf") if m == 0.0 else 20.0 * math.log10(max_val / math.sqrt(m))  # [4]

def ncc(x: np.ndarray, y: np.ndarray) -> float:
    xv = x.astype(np.float64).ravel(); yv = y.astype(np.float64).ravel()
    xv -= xv.mean(); yv -= yv.mean()
    denom = np.linalg.norm(xv) * np.linalg.norm(yv)
    return float((xv @ yv) / denom) if denom != 0.0 else 0.0  # [5]

def ssim_index(x: np.ndarray, y: np.ndarray) -> float:
    return float(ssim(x, y, channel_axis=-1, data_range=255))  # [4]

# -------- Evaluation --------
def evaluate_pair(cover_path: str, stego_path: str, side: int) -> Dict[str, float]:
    cover = load_image_bgr(cover_path)
    stego = load_image_bgr(stego_path)
    c_rs, s_rs = ensure_same_size(cover, stego, (side, side))
    return {"MSE": mse(c_rs, s_rs),
            "RMSE": rmse(c_rs, s_rs),
            "PSNR": psnr(c_rs, s_rs),
            "NCC": ncc(c_rs, s_rs),
            "SSIM": ssim_index(c_rs, s_rs)}  # [4]

def run_single_pair(cover_path: str, stego_path: str, dims: List[int]) -> Dict[int, Dict[str, float]]:
    return {d: evaluate_pair(cover_path, stego_path, d) for d in dims}  # [4]

# -------- Reporting --------
def print_table(results: Dict[int, Dict[str, float]]) -> None:
    print("Dimension |    MSE    |   RMSE   |  PSNR(dB) |    NCC    |   SSIM")
    print("-" * 70)
    for d in sorted(results):
        r = results[d]
        ps = f"{r['PSNR']:.2f}" if math.isfinite(r["PSNR"]) else "inf"
        print(f"{d}x{d}    | {r['MSE']:.6f} | {r['RMSE']:.6f} | {ps:>8} | {r['NCC']:.6f} | {r['SSIM']:.6f}")  # [4]

def save_csv(results: Dict[int, Dict[str, float]], out_csv: str) -> None:
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Dimension", "MSE", "RMSE", "PSNR(dB)", "NCC", "SSIM"])
        for d in sorted(results):
            r = results[d]
            w.writerow([f"{d}x{d}",
                        f"{r['MSE']:.6f}",
                        f"{r['RMSE']:.6f}",
                        f"{r['PSNR']:.6f}" if math.isfinite(r["PSNR"]) else "inf",
                        f"{r['NCC']:.6f}",
                        f"{r['SSIM']:.6f}"])  # [4]

# -------- CLI --------
def main():
    ap = argparse.ArgumentParser(description="Image Steganography Quality Metrics (Magic LSB)")
    ap.add_argument("--cover", required=True)
    ap.add_argument("--stego", required=True)
    ap.add_argument("--dims", nargs="+", type=int, default=[128, 256, 512, 1024])
    ap.add_argument("--out_csv", default="results/metrics_single_pair.csv")
    args = ap.parse_args()

    results = run_single_pair(args.cover, args.stego, args.dims)
    print_table(results); save_csv(results, args.out_csv)

    print("\nPSNR by dimension:")
    for d in sorted(results):
        val = results[d]["PSNR"]
        print(f"D-{d} = {val:.2f} dB" if math.isfinite(val) else f"D-{d} = inf dB")  # [4]

if __name__ == "__main__":
    main()

#python metrics.py --cover input/cover.png --stego output/stego.png --dims 128 256 512 1024
