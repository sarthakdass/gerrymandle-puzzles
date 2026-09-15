"""Bitmask Gerrymandle engine for boards with open ground.

Land tiles are either POPULATED (a house of some party) or EMPTY. A district
is a connected set of land tiles containing exactly K houses. Empty tiles
may be included as connectors/padding but never count toward K, and each
belongs to at most one district.

Only REDUCED districts are enumerated: every empty tile in a district is a
cut vertex of it (i.e. removing it would disconnect the district). Any legal
district can be reduced to this form without changing its houses, so this
loses no solutions.
"""
from hexgrid import neighbors


def popcount(x):
    return bin(x).count('1')


class Board:
    def __init__(self, land, K=5, emax=3):
        """land: dict (c,r) -> party char, or '' / None for empty land."""
        self.K = K
        self.emax = emax
        self.land = dict(land)
        self.order = sorted(land, key=lambda p: (p[1], p[0]))
        self.idx = {p: i for i, p in enumerate(self.order)}
        self.n = len(self.order)
        self.adj = [0] * self.n
        for p, i in self.idx.items():
            m = 0
            for q in neighbors(*p):
                j = self.idx.get(q)
                if j is not None:
                    m |= 1 << j
            self.adj[i] = m
        self.pop = 0
        self.pmask = {}
        for p, i in self.idx.items():
            ch = land[p]
            if ch:
                self.pop |= 1 << i
                self.pmask.setdefault(ch, 0)
                self.pmask[ch] |= 1 << i
        self.empty = ((1 << self.n) - 1) & ~self.pop
        self.nhouse = popcount(self.pop)
        assert self.nhouse % K == 0, f"{self.nhouse} houses not divisible by {K}"
        self.ND = self.nhouse // K
        self.parties = sorted(self.pmask)
        self.full = (1 << self.n) - 1
        self.cands = None

    # ---------- connectivity helper
    def connected(self, mask):
        if not mask:
            return True
        bit = mask & -mask
        seen = bit
        frontier = bit
        while frontier:
            nxt = 0
            f = frontier
            while f:
                b = f & -f; f ^= b
                nxt |= self.adj[b.bit_length() - 1]
            nxt &= mask & ~seen
            seen |= nxt
            frontier = nxt
        return seen == mask

    def reduced(self, S):
        """every empty tile in S is essential for connectivity"""
        e = S & self.empty
        while e:
            b = e & -e; e ^= b
            if self.connected(S & ~b):
                return False
        return True

    # ---------- enumerate reduced districts
    def enum_districts(self):
        K, emax = self.K, self.emax
        adj = self.adj
        pop = self.pop
        n = self.n
        out = [[] for _ in range(n)]
        for start in range(n):
            if not (pop >> start & 1):
                continue
            below = (1 << start) - 1          # tiles that cannot be reused
            avail = self.full & ~(below & pop)  # houses below start are off limits
            res = []
            def rec(S, np, ne, ext, banned):
                if np == K:
                    if self.reduced(S):
                        res.append(S)
                e = ext
                b = banned
                while e:
                    bit = e & -e
                    e ^= bit
                    v = bit.bit_length() - 1
                    isp = pop >> v & 1
                    if isp:
                        if np == K:
                            b |= bit; continue
                        nnp, nne = np + 1, ne
                    else:
                        if ne == emax:
                            b |= bit; continue
                        nnp, nne = np, ne + 1
                    new = adj[v] & avail & ~(S | b | e | bit)
                    rec(S | bit, nnp, nne, e | new, b)
                    b |= bit
            rec(1 << start, 1, 0, adj[start] & avail, 0)
            out[start] = res
        self.cands = out
        return out

    def winner(self, S):
        best = -1; who = None; tie = False
        for p, m in self.pmask.items():
            c = popcount(S & m)
            if c > best:
                best = c; who = p; tie = False
            elif c == best:
                tie = True
        return None if tie else who

    def comp_ok(self, avail):
        """every connected component of remaining land has a house count
           divisible by K"""
        K = self.K
        rem = avail
        while rem:
            bit = rem & -rem
            seen = bit; frontier = bit
            while frontier:
                nxt = 0; f = frontier
                while f:
                    b = f & -f; f ^= b
                    nxt |= self.adj[b.bit_length() - 1]
                nxt &= avail & ~seen
                seen |= nxt; frontier = nxt
            if popcount(seen & self.pop) % K:
                return False
            rem &= ~seen
        return True

    def solve(self, target=None, require_win=True, limit=None, cap=None,
              dedup=True):
        """Returns (solutions, truncated).  A solution is a list of district
        bitmasks; identity is by the house grouping."""
        if self.cands is None:
            self.enum_districts()
        seen = set()
        sols = []
        self.nodes = 0
        cands = self.cands
        pop = self.pop

        def rec(used, groups, wins, houses_left):
            if limit and len(sols) >= limit:
                return True
            if cap and self.nodes > cap:
                return True
            self.nodes += 1
            if houses_left == 0:
                if require_win:
                    t = wins.get(target, 0)
                    if not t or any(v >= t for p, v in wins.items() if p != target):
                        return False
                keyv = tuple(sorted(g & pop for g in groups))
                if dedup:
                    if keyv in seen:
                        return False
                    seen.add(keyv)
                sols.append(list(groups))
                return False
            if require_win:
                left = houses_left // self.K
                t = wins.get(target, 0) + left
                for p, v in wins.items():
                    if p != target and v >= t:
                        return False
            avail = self.full & ~used
            if not self.comp_ok(avail):
                return False
            rest = avail & pop
            start = (rest & -rest).bit_length() - 1
            for S in cands[start]:
                if S & used:
                    continue
                w = self.winner(S)
                if w:
                    nw = dict(wins); nw[w] = nw.get(w, 0) + 1
                else:
                    nw = wins
                groups.append(S)
                stop = rec(used | S, groups, nw, houses_left - self.K)
                groups.pop()
                if stop:
                    return True
            return False

        hit = rec(0, [], {}, self.nhouse)
        return sols, hit

    def cellsof(self, S):
        return [self.order[i] for i in range(self.n) if S >> i & 1]

    def tally(self, S):
        return {p: popcount(S & m) for p, m in self.pmask.items() if popcount(S & m)}
