"""Odd-r offset hex grid adjacency, shared by both engines.

Rows shift right on odd row indices ("odd-r" offset coordinates), matching
the honeycomb layout used by the reference Gerrymandle screenshots.
"""


def neighbors(c, r):
    if r % 2 == 0:
        return [(c-1, r), (c+1, r), (c-1, r-1), (c, r-1), (c-1, r+1), (c, r+1)]
    return [(c-1, r), (c+1, r), (c, r-1), (c+1, r-1), (c, r+1), (c+1, r+1)]
