import cv2
import numpy as np
import matplotlib.pyplot as plt

def rs_analysis(image_path, out_path="results/rs_plot.png"):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = img.astype(np.int16)
    n = img.size

    # Grouping pixels into pairs
    pairs = img.flatten().reshape(-1,2)

    def f(group):  # discrimination function
        return abs(group[0]-group[1])

    R, S = [], []
    for p in pairs:
        orig = f(p)
        flip = f([p[0]^1, p[1]^1])  # flip LSBs
        if flip > orig:
            R.append(1)
        elif flip < orig:
            S.append(1)

    Rm = len(R)/len(pairs)
    Sm = len(S)/len(pairs)

    plt.figure(figsize=(8,5))
    plt.plot([20,40,60,80,100],[Rm]*5,"r-",label="Rm")
    plt.plot([20,40,60,80,100],[Sm]*5,"b-",label="Sm")
    plt.xlabel("Percentage of hiding capacity")
    plt.ylabel("Fraction of groups")
    plt.title("RS Analysis")
    plt.legend()
    plt.savefig(out_path, dpi=300)
    plt.show()


# plot_histograms("input/cover.png", "output/stego.png")
# plot_pdh("input/cover.png", "output/stego.png")
# rs_analysis("output/stego.png")


rs_analysis("output/stego.png")