import numpy as np

def generate_magic_square(n: int) -> np.ndarray:
    """
    Generate an n x n magic square as a NumPy array.
    Works for odd, doubly even (n % 4 == 0), and singly even (n % 2 == 0 but not multiple of 4).
    """
    if n < 3:
        raise ValueError("Magic square not possible for n < 3")

    # Case 1: Odd order (Siamese method)
    if n % 2 == 1:
        magic = np.zeros((n, n), dtype=int)
        i, j = 0, n // 2
        for num in range(1, n * n + 1):
            magic[i, j] = num
            i, j = (i - 1) % n, (j + 1) % n
            if magic[i, j] != 0:
                i, j = (i + 2) % n, (j - 1) % n
        return magic

    # Case 2: Doubly even (n % 4 == 0)
    elif n % 4 == 0:
        magic = np.arange(1, n * n + 1).reshape(n, n)
        mask = np.full((n, n), False)
        for i in range(n):
            for j in range(n):
                if (i % 4 == j % 4) or ((i % 4 + j % 4) == 3):
                    mask[i, j] = True
        magic[mask] = n * n + 1 - magic[mask]
        return magic

    # Case 3: Singly even (n % 2 == 0 but not multiple of 4)
    else:
        half = n // 2
        sub_square = generate_magic_square(half)
        magic = np.zeros((n, n), dtype=int)

        # Fill 4 quadrants with sub-square
        add = [0, 2 * half * half, 3 * half * half, half * half]
        quadrants = [(0, 0), (0, half), (half, 0), (half, half)]
        for k, (r, c) in enumerate(quadrants):
            magic[r:r+half, c:c+half] = sub_square + add[k]

        # Swap columns
        k = (n - 2) // 4
        for i in range(half):
            for j in range(k):
                magic[i, j], magic[i+half, j] = magic[i+half, j], magic[i, j]
                magic[i, j+n-k], magic[i+half, j+n-k] = magic[i+half, j+n-k], magic[i, j+n-k]

        # Middle column swap
        for i in range(half):
            magic[i, k], magic[i+half, k] = magic[i+half, k], magic[i, k]

        return magic
