import json, math, os

P = {'P': '#a855f7', 'G': '#22c55e', 'O': '#f59e0b', 'C': '#38bdf8',
     'R': '#fb7185', 'B': '#6366f1'}
FILL = {'P': '#2a1442', 'G': '#0f3520', 'O': '#3a2506', 'C': '#07293d',
        'R': '#3d1520', 'B': '#1b1d4a'}
NAMEC = {'P': 'purple', 'G': 'green', 'O': 'amber', 'C': 'cyan',
         'R': 'rose', 'B': 'indigo'}
ORDER = ['P', 'G', 'O', 'C', 'R', 'B']
S = 26.0
SQ3 = math.sqrt(3)


def center(c, r):
    return (S * SQ3 * (c + 0.5 * (r & 1)), S * 1.5 * r)


def verts(c, r, s=S):
    x, y = center(c, r)
    return [(x + s * math.cos(math.radians(60 * i - 30)),
             y + s * math.sin(math.radians(60 * i - 30))) for i in range(6)]


def poly(c, r, s=S):
    return ' '.join(f'{x:.2f},{y:.2f}' for x, y in verts(c, r, s))


def svg(land, sol=None):
    keys = list(land)
    xs, ys = [], []
    for c, r in keys:
        for x, y in verts(c, r):
            xs.append(x); ys.append(y)
    pad = 14
    minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad

    dist_of, win_of = {}, {}
    if sol:
        for i, d in enumerate(sol):
            cnt = {}
            for t in d:
                ch = land[tuple(t)]
                if ch:
                    cnt[ch] = cnt.get(ch, 0) + 1
            best = max(cnt.values())
            tops = [p for p, v in cnt.items() if v == best]
            win_of[i] = tops[0] if len(tops) == 1 else None
            for t in d:
                dist_of[tuple(t)] = i

    o = [f'<svg viewBox="{minx:.1f} {miny:.1f} {maxx-minx:.1f} {maxy-miny:.1f}" '
         f'xmlns="http://www.w3.org/2000/svg" class="map" role="img">']
    for (c, r) in keys:
        i = dist_of.get((c, r))
        if sol and i is not None:
            fill = FILL.get(win_of[i], '#1f2a3d')
        else:
            fill = '#1b2334' if land[(c, r)] else '#141b29'
        o.append(f'<polygon points="{poly(c,r)}" fill="{fill}" stroke="#0a0e18" stroke-width="2"/>')
    for (c, r), ch in land.items():
        x, y = center(c, r)
        if ch:
            s = S * 0.34
            pts = ' '.join(f'{x+s*math.cos(math.radians(60*i-30)):.2f},'
                           f'{y+s*math.sin(math.radians(60*i-30)):.2f}' for i in range(6))
            o.append(f'<polygon points="{pts}" fill="{P[ch]}"/>')
        else:
            s = S * 0.30
            pts = ' '.join(f'{x+s*math.cos(math.radians(60*i-30)):.2f},'
                           f'{y+s*math.sin(math.radians(60*i-30)):.2f}' for i in range(6))
            o.append(f'<polygon points="{pts}" fill="none" stroke="#33415c" '
                     f'stroke-width="2" stroke-dasharray="3 3"/>')
    if sol:
        for (c, r) in keys:
            if (c, r) not in dist_of:
                continue
            i = dist_of[(c, r)]
            col = P.get(win_of[i]) or '#94a3b8'
            v = verts(c, r)
            cx, cy = center(c, r)
            for k in range(6):
                a, b = v[k], v[(k + 1) % 6]
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                nx, ny = cx + 2 * (mx - cx), cy + 2 * (my - cy)
                same = False
                for (c2, r2) in keys:
                    if dist_of.get((c2, r2)) != i or (c2, r2) == (c, r):
                        continue
                    x2, y2 = center(c2, r2)
                    if abs(x2 - nx) < 1.5 and abs(y2 - ny) < 1.5:
                        same = True; break
                if not same:
                    d = 3.6
                    ux, uy = cx - mx, cy - my
                    L = math.hypot(ux, uy) or 1
                    ux, uy = ux / L * d, uy / L * d
                    o.append(f'<line x1="{a[0]+ux:.2f}" y1="{a[1]+uy:.2f}" '
                             f'x2="{b[0]+ux:.2f}" y2="{b[1]+uy:.2f}" stroke="{col}" '
                             f'stroke-width="4" stroke-linecap="round"/>')
    o.append('</svg>')
    return '\n'.join(o)


def ascii_map(land):
    maxr = max(r for c, r in land); maxc = max(c for c, r in land)
    out = []
    for r in range(maxr + 1):
        line = '  ' if r % 2 else ''
        for c in range(maxc + 1):
            if (c, r) in land:
                line += (land[(c, r)] or '-').ljust(4)
            else:
                line += '.'.ljust(4)
        out.append(line.rstrip())
    return '\n'.join(out)


def bar(voters):
    tot = sum(voters.values())
    seg = []
    for p in ORDER:
        if p in voters:
            seg.append(f'<span class="seg" style="width:{100*voters[p]/tot:.2f}%;'
                       f'background:{P[p]}">{voters[p]}</span>')
    return '<div class="bar">' + ''.join(seg) + '</div>'


def result_line(oc):
    bits = []
    for p, n in sorted(oc.items(), key=lambda x: (-x[1], x[0])):
        who = 'nobody' if p == 'DEAD' else NAMEC[p]
        bits.append(f'{n} to {who}')
    return ', '.join(bits)


TITLE = {
 'A': 'Four&ndash;two', 'B': 'The dead heat', 'C': 'The ring', 'D': 'The isthmus',
 'E': 'Five graves', 'F': 'Even split', 'G': 'Heavy districts',
 'H': 'Four-way', 'I': 'One seat, six houses',
 'Q': 'Four by four', 'J': 'Two districts', 'N': 'Five parties',
 'M': 'Six to a district', 'L': 'All six', 'K': 'Ten districts',
}

BLURB = {
 'A': ("Six districts, and purple holds 13 of the 30 houses, so it needs four of them. "
       "Of the 34,224 legal cuts, 10,841 finish 3&ndash;2&ndash;1 style deadlocks at 3&ndash;3. "
       "One finishes 4&ndash;2."),
 'B': ("Three parties, seven districts, purple smallest at nine houses. Purple wins exactly "
       "one district and takes the election, because the other six have to be deadlocked so "
       "that neither green nor amber can take a single one."),
 'C': ("The land is a hexagonal annulus two tiles thick, so every district is forced to run "
       "along the band. Only 168 legal cuts exist, and 145 of them finish 3&ndash;3."),
 'D': ("Eight districts, purple down 17&ndash;23 and needing five. Two dense clusters joined "
       "by a thin neck, and the answer turns on which side spends houses on a throwaway "
       "green district."),
 'E': ("Ten houses each for three parties, and seven patches of open ground. Purple takes a "
       "single district; the other five are deliberately tied and die. The open tiles are "
       "what make it possible &mdash; several districts only reach their houses by stepping "
       "across vacant land."),
 'F': ("Four houses per district changes the game: a district can split 2&ndash;2, so even "
       "with only two parties on the board, districts can die. Purple takes three, green two, "
       "and two are killed off. 4,651 of the legal cuts leave purple tied."),
 'G': ("Seven houses per district and only five districts, so each one is a heavy commitment "
       "and mistakes are unrecoverable. Purple takes two, which is enough because green and "
       "amber are held to one apiece and the fifth district dies."),
 'H': ("Four parties, six houses each, three houses per district. A district can split "
       "1&ndash;1&ndash;1 and die, and three of them do. Purple needs only two of the eight "
       "to finish clear of everyone."),
 'I': ("Six houses per district across five districts. Purple holds nine of thirty houses and "
       "wins one district while the other four are tied dead. The narrowest margin here: only "
       "58 of the 2,066 legal cuts even leave purple level."),
 'Q': ("The smallest board here: twelve houses on four rows, three parties, three districts. "
       "Only 53 legal cuts exist and 41 of them leave purple level, so almost every move you "
       "can make is a draw. Purple takes two districts and kills the third."),
 'J': ("Two districts of seven houses, and purple is the smallest party with four. Purple "
       "cannot win both &mdash; it wins one and forces the other into a three-way stall that "
       "green and amber split evenly. One district to purple, none to anyone else."),
 'N': ("Five parties, four houses each, five districts. With four houses to a district a "
       "2&ndash;2 split is fatal, and four of the five districts end that way. Purple takes "
       "the one that doesn't."),
 'M': ("Two parties but six houses per district, so a 3&ndash;3 split kills a district "
       "outright. Purple is down 11&ndash;13 and still finishes ahead: two districts to "
       "purple, one to green, and one buried at three apiece."),
 'L': ("Every party holds exactly five houses and every district holds exactly five houses, "
       "so nothing is decided by arithmetic &mdash; only by where the lines fall. Purple wins "
       "a single district and all five others deadlock. The hardest of the new set: 11,530 of "
       "the 17,895 legal cuts leave purple tied rather than ahead."),
 'K': ("Ten districts of three houses across four parties. Districts are tiny, so a "
       "1&ndash;1&ndash;1 stall is always one bad tile away, and three of them happen. Purple "
       "takes three, green and cyan two each."),
}

SEC1 = ("Every tile on these four boards holds a house, so districts are simply connected "
        "groups of houses.")
SEC2 = ("These five boards have open ground: tiles that are part of the map and can be taken "
        "into a district, but hold no house. They are stepping stones. A district can reach "
        "across them to pick up houses it could not otherwise touch, and it can also ignore "
        "them entirely.")
SEC3 = ("These six push on the other dials: board size, how many parties are running, and how "
        "many houses go in a district. They run from a twelve-house board settled in three "
        "districts up to ten districts of three houses, and from three parties up to six. "
        "Bigger districts and more parties both make dead heats easier to engineer, which is "
        "usually how purple gets in.")


def block(z, k, land, sol, extra_chips):
    v = z['voters']; tot = sum(v.values())
    parts = ' &middot; '.join(f"{v[p]} {NAMEC[p]}" for p in ORDER if p in v)
    pad = z.get('paddings')
    padline = ''
    if pad is not None:
        padline = ('<dt>Open tiles used by the answer</dt><dd>' +
                   ('forced &mdash; no alternative' if pad == 1 else
                    f'{pad} equivalent paddings') + '</dd>')
    chips = ''.join(f'<span class="chip">{c}</span>' for c in extra_chips)
    return f'''
<section class="puzzle" id="p{k}">
  <header class="phead">
    <h2>{TITLE[z['name']]}</h2>
    <div class="chips">{chips}</div>
    <p class="obj">Draw {z['ndist']} districts of {z['K']} houses each so that purple wins
       more districts than any other party.</p>
  </header>
  <div class="grid">
    <div class="mapwrap">
      <div class="stage">
        <div class="layer show" data-view="puzzle">{svg(land)}</div>
        <div class="layer" data-view="solution">{svg(land, sol)}</div>
      </div>
      <button class="toggle" data-target="p{k}">Show the solution</button>
    </div>
    <aside class="dossier">
      {bar(v)}
      <p class="vline">{parts} &mdash; {tot} houses across {z['ndist']} districts</p>
      <dl>
        <dt>Legal ways to group the houses</dt><dd>{z['total']:,}</dd>
        <dt>Of those, purple wins</dt><dd class="hit">exactly 1</dd>
        <dt>Cuts leaving purple tied for the lead</dt><dd>{z['ties']:,}</dd>
        <dt>Cuts where purple simply loses</dt><dd>{z['losses']:,}</dd>
        <dt>The winning split</dt><dd>{result_line(z['outcomes'])}</dd>
        {padline}
      </dl>
      <p class="note">{BLURB[z['name']]}</p>
      <details><summary>Board as text</summary><pre>{ascii_map(land)}</pre></details>
    </aside>
  </div>
</section>'''


def dims(land):
    cols = [c for c, r in land]; rows = [r for c, r in land]
    return max(cols) - min(cols) + 1, max(rows) - min(rows) + 1


def main():
    solid = json.load(open('data/solid_puzzles.json'))
    open_g = json.load(open('data/open_puzzles.json'))
    varied = json.load(open('data/varied_puzzles.json'))
    order = {'E': 0, 'F': 1, 'G': 2, 'H': 3, 'I': 4}
    open_g.sort(key=lambda z: order[z['name']])
    vorder = {'Q': 0, 'J': 1, 'N': 2, 'M': 3, 'L': 4, 'K': 5}
    varied.sort(key=lambda z: vorder[z['name']])

    blocks1, blocks2, blocks3 = [], [], []
    k = 0
    for z in solid:
        k += 1
        land = {(c, r): ch for c, r, ch in z['cells']}
        sol = [[tuple(t) for t in d] for d in z['sol']]
        w, h = dims(land)
        chips = [f"{z['K']} houses per district", f"{len(z['voters'])} parties",
                 f"{z['ndist']} districts", f"{w}&times;{h} board"]
        blocks1.append(block(z, k, land, sol, chips))
    for z in open_g:
        k += 1
        land = {(c, r): ch for c, r, ch in z['land']}
        sol = [[tuple(t) for t in d] for d in z['sol']]
        w, h = dims(land)
        chips = [f"{z['K']} houses per district", f"{len(z['voters'])} parties",
                 f"{z['ndist']} districts", f"{z['nempty']} open tiles",
                 f"{w}&times;{h} board"]
        blocks2.append(block(z, k, land, sol, chips))
    for z in varied:
        k += 1
        land = {(c, r): ch for c, r, ch in z['land']}
        sol = [[tuple(t) for t in d] for d in z['sol']]
        w, h = dims(land)
        chips = [f"{z['K']} houses per district", f"{len(z['voters'])} parties",
                 f"{z['ndist']} districts", f"{z['nempty']} open tiles",
                 f"{w}&times;{h} board"]
        blocks3.append(block(z, k, land, sol, chips))

    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fifteen Gerrymandle boards with exactly one purple win</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#080c16;--panel:#0e1524;--line:#1e2940;--ink:#dbe3f0;--dim:#7c8aa5;--purple:#a855f7}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.6 Barlow,system-ui,sans-serif;
-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1120px;margin:0 auto;padding:64px 28px 96px}}
.lede{{max-width:62ch}}
h1{{font:600 44px/1.1 'Barlow Semi Condensed',Barlow,sans-serif;margin:0 0 18px}}
h1 .p{{color:var(--purple)}}
.lede p{{color:var(--dim);margin:0 0 14px}}
.rules{{margin:34px 0 0;padding:20px 24px;background:var(--panel);border:1px solid var(--line);
border-radius:14px;max-width:70ch}}
.rules p{{margin:0 0 10px;font-size:15.5px;color:var(--dim)}}
.rules p:last-child{{margin:0}}
.rules b{{color:var(--ink);font-weight:600}}
.secthead{{margin:88px 0 0;padding-top:30px;border-top:2px solid var(--line)}}
.secthead h2{{font:600 27px/1.2 'Barlow Semi Condensed',Barlow,sans-serif;margin:0 0 10px}}
.secthead p{{margin:0;color:var(--dim);max-width:66ch;font-size:15.5px}}
.puzzle{{margin-top:64px;padding-top:34px;border-top:1px solid var(--line)}}
.phead h2{{font:600 30px/1.15 'Barlow Semi Condensed',Barlow,sans-serif;margin:0 0 10px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.chip{{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:13.5px;
color:var(--dim)}}
.obj{{margin:0 0 26px;color:var(--dim);max-width:60ch;font-size:16px}}
.grid{{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:40px;align-items:start}}
.stage{{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:14px;
padding:18px;display:flex;align-items:center;justify-content:center;min-height:300px}}
.layer{{display:none;width:100%}}
.layer.show{{display:block}}
.map{{width:100%;height:auto;display:block}}
.toggle{{margin-top:14px;width:100%;padding:12px 16px;background:transparent;color:var(--ink);
border:1px solid var(--line);border-radius:10px;font:500 15px Barlow,sans-serif;cursor:pointer}}
.toggle:hover{{border-color:var(--purple);color:#fff}}
.toggle:focus-visible{{outline:2px solid var(--purple);outline-offset:2px}}
.bar{{display:flex;height:26px;border-radius:7px;overflow:hidden;margin-bottom:10px}}
.seg{{display:flex;align-items:center;justify-content:center;color:#08101c;
font:600 13px 'Barlow Semi Condensed',sans-serif}}
.vline{{margin:0 0 20px;color:var(--dim);font-size:14.5px}}
dl{{margin:0 0 20px;border-top:1px solid var(--line)}}
dt{{color:var(--dim);font-size:14.5px;padding-top:11px}}
dd{{margin:0 0 11px;padding-bottom:11px;border-bottom:1px solid var(--line);
font:600 19px 'Barlow Semi Condensed',sans-serif}}
dd.hit{{color:var(--purple)}}
.note{{font-size:15.5px;color:var(--dim);margin:0 0 16px}}
details{{font-size:14px;color:var(--dim)}}
summary{{cursor:pointer;padding:6px 0}}
pre{{background:#070b13;border:1px solid var(--line);border-radius:10px;padding:14px;
overflow:auto;font-size:13px;line-height:1.5;color:#93a2ba}}
@media(max-width:860px){{.grid{{grid-template-columns:1fr;gap:26px}}h1{{font-size:34px}}
.wrap{{padding:40px 18px 64px}}}}
</style></head><body><div class="wrap">
<h1>Fifteen Gerrymandle boards with exactly one <span class="p">purple</span> win</h1>
<div class="lede">
<p>Every board here was searched exhaustively: all legal ways of cutting it were enumerated,
and in each case precisely one of them puts purple ahead. No second answer, no
near-equivalent answer.</p>
<p>The counts beside each map are the real search space, not estimates.</p>
</div>
<div class="rules">
<p><b>Districts.</b> A district is a connected group of tiles holding exactly the stated
number of houses. Tiles touch along hex edges.</p>
<p><b>Open ground.</b> Tiles drawn with a dashed centre hold no house. A district may take
them in &mdash; to reach around an obstacle or bridge a gap &mdash; or leave them out. They
never count toward the house total, and each one can belong to at most one district. Open
ground left over at the end is simply unassigned.</p>
<p><b>Winning.</b> A party takes a district by holding strictly more houses in it than any
other party. An even split leaves the district <b>dead</b>: nobody takes it. A party wins the
election by taking more districts than every other party.</p>
</div>
<div class="secthead"><h2>Solid boards</h2><p>{SEC1}</p></div>
{''.join(blocks1)}
<div class="secthead"><h2>Boards with open ground</h2><p>{SEC2}</p></div>
{''.join(blocks2)}
<div class="secthead"><h2>Other sizes, parties and district sizes</h2><p>{SEC3}</p></div>
{''.join(blocks3)}
</div>
<script>
document.querySelectorAll('.toggle').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    var s = document.getElementById(btn.dataset.target).querySelector('.stage');
    var show = s.querySelector('.layer.show').dataset.view === 'puzzle';
    s.querySelectorAll('.layer').forEach(function(l){{
      l.classList.toggle('show', (l.dataset.view === 'solution') === show);
    }});
    btn.textContent = show ? 'Hide the solution' : 'Show the solution';
  }});
}});
</script>
</body></html>'''
    os.makedirs('site', exist_ok=True)
    open('site/gerrymandle-boards.html', 'w').write(html)
    print('written', len(html))


main()
