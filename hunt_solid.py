"""Search for solid boards (no open ground) that have exactly one way for
the target party to win the election, out of every legal partition.

Usage as a library:
    from hunt_solid import hunt
    found, tried, elapsed = hunt({'P': 13, 'G': 17}, 'P', tries=100000)

Each `found` entry is (cells, solution) where cells is a dict (c,r)->party
and solution is a list of district bitmasks straight from engine_solid.Board.
"""
import random
import time

from engine_solid import Board
from hexgrid import neighbors


def grow(n, rng, W=11, H=9, alpha=-1.2):
    """Grow a connected blob of n tiles by random accretion.
    alpha<0 favours low-degree cells, producing stringier, harder shapes;
    alpha>0 favours already-dense cells, producing rounder blobs."""
    start = (rng.randrange(2, W - 2), rng.randrange(2, H - 2))
    S = {start}
    while len(S) < n:
        fr = {}
        for p in S:
            for q in neighbors(*p):
                if q in S:
                    continue
                if not (0 <= q[0] < W and 0 <= q[1] < H):
                    continue
                fr[q] = sum(1 for z in neighbors(*q) if z in S)
        if not fr:
            return None
        ks = list(fr)
        ws = [max(fr[k], 1) ** alpha for k in ks]
        S.add(rng.choices(ks, weights=ws)[0])
    return S


def hunt(mix, target, K=5, tries=100000, seed=1, W=11, H=9, alpha=-1.2,
         per_layout=6, tlimit=300, verbose=True):
    """mix: dict party -> house count. Must sum to a multiple of K."""
    n = sum(mix.values())
    pool = []
    for p, k in mix.items():
        pool += [p] * k
    rng = random.Random(seed)
    t0 = time.time()
    found = []
    t = 0
    while t < tries and time.time() - t0 < tlimit:
        S = grow(n, rng, W, H, alpha)
        if S is None:
            continue
        pts = sorted(S, key=lambda p: (p[1], p[0]))
        for _ in range(per_layout):
            t += 1
            rng.shuffle(pool)
            cells = dict(zip(pts, pool))
            b = Board(cells, K=K)
            sols, _ = b.solve(target=target, limit=2, cap=4_000_000)
            if len(sols) == 1:
                found.append((dict(cells), sols[0]))
                if verbose:
                    print(f"   unique @try {t} ({time.time()-t0:.0f}s)")
    return found, t, time.time() - t0


if __name__ == '__main__':
    # small demo: search for a 30-tile, 2-party board
    found, tried, elapsed = hunt({'P': 13, 'G': 17}, 'P', tries=5000,
                                 tlimit=30, seed=0)
    print(f"{len(found)} unique-solution boards found in {tried} tries "
          f"({elapsed:.0f}s)")
