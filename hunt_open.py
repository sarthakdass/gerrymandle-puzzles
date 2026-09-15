"""Search for boards WITH open ground that have exactly one way for the
target party to win the election, out of every legal grouping of houses.

Usage as a library:
    from hunt_open import run
    run('found.jsonl', seed=1, budget=120, mix={'P': 10, 'G': 10, 'O': 10},
        target='P', K=5, nempty=7, W=11, H=9, alpha=0.7, emax=2)

Results are appended to the given .jsonl file, one JSON object per unique
board found, each already re-certified with an uncapped, unlimited search
(no `cap`/`limit` truncation) so `total` is an exact count.
"""
import json
import random
import sys
import time

from engine_open import Board
from hexgrid import neighbors


def grow(n, rng, W, H, alpha=0.7):
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


def make_board(rng, nh, nempty, W, H, alpha, mix, K, emax):
    """Grow a blob of nh+nempty tiles, pick nempty *interior* tiles (ones
    fully surrounded by other blob tiles) to leave empty, and colour the
    rest with the party mix."""
    S = grow(nh + nempty, rng, W, H, alpha)
    if S is None:
        return None
    interior = [p for p in S if all(q in S for q in neighbors(*p))]
    if len(interior) < nempty:
        return None
    empties = set(rng.sample(interior, nempty))
    houses = sorted(S - empties, key=lambda p: (p[1], p[0]))
    if len(houses) != nh:
        return None
    pool = []
    for p, k in mix.items():
        pool += [p] * k
    rng.shuffle(pool)
    land = {p: '' for p in empties}
    land.update(dict(zip(houses, pool)))
    try:
        return Board(land, K=K, emax=emax)
    except AssertionError:
        return None


def run(out_f, seed, budget, mix, target, K, nempty, W, H, alpha, emax,
        mincands=0, maxcands=400000):
    nh = sum(mix.values())
    rng = random.Random(seed)
    OUT = open(out_f, 'a')
    t0 = time.time()
    tried = 0
    kept = 0
    while time.time() - t0 < budget:
        b = make_board(rng, nh, nempty, W, H, alpha, mix, K, emax)
        if b is None:
            continue
        tried += 1
        b.enum_districts()
        nc = sum(len(x) for x in b.cands)
        if nc > maxcands or nc < mincands:
            continue
        # quick screen with a node cap, then re-certify uncapped before saving
        sols, hit = b.solve(target=target, limit=2, cap=2_000_000)
        if hit or len(sols) != 1:
            continue
        sols2, hit2 = b.solve(target=target)
        if hit2 or len(sols2) != 1:
            continue
        allp, trunc = b.solve(require_win=False, cap=1_200_000)
        ties = 0
        for s in allp:
            w = {}
            for g in s:
                x = b.winner(g)
                if x:
                    w[x] = w.get(x, 0) + 1
            t = w.get(target, 0)
            o = max([v for p, v in w.items() if p != target] + [0])
            if t == o and t > 0:
                ties += 1
        oc = {}
        for g in sols2[0]:
            x = b.winner(g)
            oc[x or 'DEAD'] = oc.get(x or 'DEAD', 0) + 1
        OUT.write(json.dumps({
            'land': [[c, r, ch] for (c, r), ch in b.land.items()],
            'sol': [sorted(b.cellsof(g)) for g in sols2[0]],
            'K': K, 'target': target, 'mix': mix, 'ndist': b.ND,
            'total': len(allp), 'total_trunc': trunc, 'ties': ties,
            'outcomes': oc, 'nempty': nempty, 'emax': emax,
        }) + '\n')
        OUT.flush()
        kept += 1
    print('tried', tried, 'kept', kept)


if __name__ == '__main__':
    # e.g.: python3 hunt_open.py out.jsonl 1 120 '{"P":10,"G":10,"O":10}' P 5 7 11 9 0.7 2
    a = sys.argv
    run(a[1], int(a[2]), float(a[3]), json.loads(a[4]), a[5], int(a[6]),
        int(a[7]), int(a[8]), int(a[9]), float(a[10]), int(a[11]))
