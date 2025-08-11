# helper: magic square generator (odd n) and small utilities
def generate_magic_square(n: int):
    """
    Return an n x n magic square (Siamese method) for odd n.
    """
    if n % 2 == 0:
        raise ValueError("Magic square generator only supports odd n here.")
    magic = [[0] * n for _ in range(n)]
    num = 1
    i, j = 0, n // 2
    while num <= n * n:
        magic[i][j] = num
        num += 1
        ni, nj = (i - 1) % n, (j + 1) % n
        if magic[ni][nj]:
            i = (i + 1) % n
        else:
            i, j = ni, nj
    return magic
