# Gerrymandle puzzle generator

Fifteen hand-picked Gerrymandle boards, each with a solution certified by
exhaustive search: every legal way of cutting the board into districts was
enumerated, and exactly one of them wins the election for purple. The
generated page is at `site/gerrymandle-boards.html`.

The set spans boards from 4x4 up to 8x9, 2 to 10 districts, 3 to 6 parties,
and 3 to 7 houses per district. Six party colours are supported: purple (P),
green (G), amber (O), cyan (C), rose (R) and indigo (B). Purple is the target
party on every board.

## Rules modeled

- A district is a connected group of tiles (hex, edge-adjacency) containing
  exactly K houses.
- Two board types are supported:
  - **Solid boards** (`engine_solid.py`) — every tile holds a house. A
    district is just K connected tiles.
  - **Open-ground boards** (`engine_open.py`) — some tiles are empty land.
    A district may cross empty tiles to connect houses that aren't
    otherwise adjacent, but empty tiles never count toward K and each
    belongs to at most one district.
- A party wins a district by holding strictly more houses in it than any
  other party. A tie means nobody wins that district.
- The target party wins the election by winning more districts than every
  other party.

## Files

- `hexgrid.py` — shared hex adjacency (odd-r offset coordinates).
- `engine_solid.py` — bitmask solver for solid boards (class `Board`).
- `engine_open.py` — bitmask solver for boards with open ground (class
  `Board`). Only enumerates *reduced* districts (every empty tile included
  is load-bearing for connectivity) — this loses no solutions but keeps the
  search tractable.
- `hunt_solid.py` / `hunt_open.py` — random layout + coloring search that
  looks for boards with **exactly one** winning partition for the target
  party. Both re-certify any hit with an uncapped, unlimited search before
  accepting it.
- `data/solid_puzzles.json`, `data/open_puzzles.json`,
  `data/varied_puzzles.json` — the fifteen chosen puzzles, one file per
  section of the page: board layout, voter counts, the unique winning
  solution, and exhaustive search statistics (total legal partitions, how
  many end in a tie, how many are outright losses). `varied_puzzles.json`
  holds the boards that vary size, party count and district size.
- `generate_site.py` — renders the JSON puzzle data into the HTML page in
  `site/`.

## Regenerating the page

```
python3 generate_site.py
```

Reads `data/*.json`, writes `site/gerrymandle-boards.html`.

## Searching for new puzzles

```python
from hunt_solid import hunt
found, tried, elapsed = hunt({'P': 13, 'G': 17}, 'P', K=5, tries=100000, tlimit=120)
```

```python
from hunt_open import run
run('out.jsonl', seed=1, budget=120, mix={'P': 10, 'G': 10, 'O': 10},
    target='P', K=5, nempty=7, W=11, H=9, alpha=0.7, emax=2)
```

`hunt_open.run` appends any hit (already re-certified uncapped) as one JSON
line to the given file. Each hit records the board, the winning solution,
and the full search statistics — the same shape as the entries in
`data/open_puzzles.json`.

Both searches are randomized and can take anywhere from seconds to minutes
to find a board with exactly one winning partition, depending on how tight
the constraints are (small boards / large parties / big K all make hits
rarer).
