import cv2
import numpy as np
import matplotlib.pyplot as plt

def rs_analysis(image_path, block_size=2):
    # Load grayscale image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Flatten into 1D array
    pixels = img.flatten()

    # Group pixels into non-overlapping blocks
    n_blocks = len(pixels) // block_size
    pixels = pixels[:n_blocks * block_size].reshape(n_blocks, block_size)

    # Discriminant function (sum of absolute differences)
    def f(block):
        return np.sum(np.abs(np.diff(block)))

    # Flip mask
    mask = np.array([1, -1] * (block_size // 2))

    R, Rm, S, Sm = [], [], [], []

    # Loop over embedding rates (0–100%)
    for p in range(0, 101, 10):
        n_flips = int((p / 100.0) * n_blocks)
        indices = np.random.choice(n_blocks, n_flips, replace=False)
        modified = pixels.copy()

        # Apply flipping
        modified[indices] = np.clip(modified[indices] + mask, 0, 255)

        # Count Regular (R) and Singular (S) groups
        F_orig = np.array([f(b) for b in pixels])
        F_mod = np.array([f(b) for b in modified])

        R_count = np.sum(F_mod > F_orig)
        S_count = np.sum(F_mod < F_orig)

        R.append(R_count / n_blocks)
        S.append(S_count / n_blocks)

        # For negative flipping
        modified_neg = pixels.copy()
        modified_neg[indices] = np.clip(modified_neg[indices] - mask, 0, 255)
        F_mod_neg = np.array([f(b) for b in modified_neg])

        Rm_count = np.sum(F_mod_neg > F_orig)
        Sm_count = np.sum(F_mod_neg < F_orig)

        Rm.append(Rm_count / n_blocks)
        Sm.append(Sm_count / n_blocks)

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(range(0, 101, 10), R, 'r-', label="R(p)")
    plt.plot(range(0, 101, 10), Rm, 'r--', label="R(-p)")
    plt.plot(range(0, 101, 10), S, 'b-', label="S(p)")
    plt.plot(range(0, 101, 10), Sm, 'b--', label="S(-p)")
    plt.xlabel("Percentage of Hiding Capacity")
    plt.ylabel("Fraction of Regular & Singular Groups")
    plt.title("RS Steganalysis")
    plt.legend()
    plt.grid(True)
    plt.show()

# Example usage
rs_analysis("output/stego.png")
