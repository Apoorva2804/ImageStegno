import cv2
import matplotlib.pyplot as plt

def plot_histograms(cover_path, stego_path, out_path="results/histograms.png"):
    cover = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)

    # histograms
    cover_hist = cv2.calcHist([cover],[0],None,[256],[0,256])
    stego_hist = cv2.calcHist([stego],[0],None,[256],[0,256])

    plt.figure(figsize=(10,5))
    plt.plot(cover_hist, color="blue", label="Cover Image")
    plt.plot(stego_hist, color="red", linestyle="--", label="Stego Image")
    plt.title("Histogram Comparison")
    plt.xlabel("Pixel Intensity")
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig(out_path, dpi=300)
    plt.show()


plot_histograms("input/cover.png", "output/stego.png")