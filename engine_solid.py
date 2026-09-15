"""Bitmask Gerrymandle engine for solid boards (every tile is populated).

A district is a connected set of exactly K tiles. Enumerates every legal
way to partition the board and checks which ones give the target party
strictly more district wins than any other party.
"""
from hexgrid import neighbors


class Board:
    def __init__(self, cells, K=5):
        self.cells = dict(cells)
        self.K = K
        self.order = sorted(cells, key=lambda p: (p[1], p[0]))
        self.idx = {p: i for i, p in enumerate(self.order)}
        self.n = len(self.order)
        self.ND = self.n // K
        self.adj = [0] * self.n
        for p, i in self.idx.items():
            m = 0
            for q in neighbors(*p):
                j = self.idx.get(q)
                if j is not None:
                    m |= 1 << j
            self.adj[i] = m
        self.parties = sorted(set(cells.values()))
        self.pmask = {}
        for p in self.parties:
            m = 0
            for q, i in self.idx.items():
                if cells[q] == p:
                    m |= 1 << i
            self.pmask[p] = m
        self.full = (1 << self.n) - 1

    # ------------------------------------------------ connected K-subsets
    def ksubs(self, start, avail):
        K = self.K
        adj = self.adj
        out = []
        ap = out.append
        def rec(sub, cnt, ext, banned):
            if cnt == K:
                ap(sub); return
            e = ext
            b = banned
            while e:
                bit = e & -e
                e ^= bit
                v = bit.bit_length() - 1
                new = adj[v] & avail & ~(sub | b | e | bit)
                rec(sub | bit, cnt + 1, e | new, b)
                b |= bit
        rec(1 << start, 1, self.adj[start] & avail, 0)
        return out

    def comp_ok(self, avail):
        K = self.K
        adj = self.adj
        rem = avail
        while rem:
            bit = rem & -rem
            seen = bit
            frontier = bit
            while frontier:
                nxt = 0
                f = frontier
                while f:
                    b2 = f & -f
                    f ^= b2
                    nxt |= adj[b2.bit_length() - 1]
                nxt &= avail & ~seen
                seen |= nxt
                frontier = nxt
            if bin(seen).count('1') % K:
                return False
            rem &= ~seen
        return True

    def winner(self, sub):
        best = -1; who = None; tie = False
        for p, m in self.pmask.items():
            c = bin(sub & m).count('1')
            if c > best:
                best = c; who = p; tie = False
            elif c == best:
                tie = True
        return None if tie else who

    def solve(self, target=None, limit=None, require_win=True, cap=None):
        sols = []
        self.nodes = 0
        def rec(avail, groups, wins):
            if limit and len(sols) >= limit:
                return True
            if cap and self.nodes > cap:
                return True
            self.nodes += 1
            if not avail:
                if not require_win:
                    sols.append(list(groups)); return False
                t = wins.get(target, 0)
                if t and all(v < t for p, v in wins.items() if p != target):
                    sols.append(list(groups))
                return False
            if require_win:
                left = bin(avail).count('1') // self.K
                t = wins.get(target, 0) + left
                for p, v in wins.items():
                    if p != target and v >= t:
                        return False
            if not self.comp_ok(avail):
                return False
            start = (avail & -avail).bit_length() - 1
            for sub in self.ksubs(start, avail):
                w = self.winner(sub)
                if w:
                    nw = dict(wins); nw[w] = nw.get(w, 0) + 1
                else:
                    nw = wins
                groups.append(sub)
                stop = rec(avail & ~sub, groups, nw)
                groups.pop()
                if stop:
                    return True
            return False
        hit = rec(self.full, [], {})
        return sols, hit

    def tally(self, sub):
        return {p: bin(sub & m).count('1') for p, m in self.pmask.items()}

    def cellsof(self, sub):
        return [self.order[i] for i in range(self.n) if sub >> i & 1]
