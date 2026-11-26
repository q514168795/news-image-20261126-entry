# news-image-20261126-entry

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/q514168795/news-image-20261126-entry/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/q514168795/news-image-20261126-entry/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

Entry for make.fun's [Sum up 26 November's world news in one image](https://make.fun/bounty/news-image-20261126) competition ($100 USDC).

## What it builds

A 1024×1024 broadsheet-style infographic summarizing **45 dated world news stories from Thursday 26 November 2026** across **9 regions** and **19 fields**:

- **Masthead & Taxonomy**: Proportional 9-region ribbon, 19-field counter strip, and 5-column Day-in-Numbers KPI bar (`3.25%`, `$50B`, `100th`, `2`, `4.9%`).
- **Tier 1 (3 Hero Cards, #1–#3)**: Bank of Korea 3.25% rate hike & 3.9% GDP upgrade, Kim Jong Un tactical nuclear rollout order, and Saudi coalition missile interception over Riyadh & Sanaa blast — each with bespoke high-contrast inline-SVG art, certainty tags, and `WHY IT MATTERS` synthesis.
- **Tier 2 (10 Secondary Illustrated Cards, #4–#13)**: Original flat-vector scenes covering New York, Geneva/Gaza, Brussels, Jakarta, Tokyo, Lusaka, Canberra, London, São Paulo, and Dimorphos (DART crater).
- **Tier 3 (World Map & 32 Dated Briefs, #14–#45)**: Custom vector world map with collision-free numbered pins (`1–12`), a framed `GLOBAL & SPACE` inset (`13`, `#45`), and two balanced 16-item brief columns.
- **Editorial Audit Footer**: Explicit `DATE CHECK` listing excluded Wednesday 25 November stories, epistemic certainty key (`OFFICIAL`, `REPORTED`, `CLAIM`), and wire source credits.

## Usage

Run the deterministic Python 3.13 entrypoint (zero network, stdlib only):

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Regenerate `entry.png` locally from `render_frontpage.py`:

```bash
python3 render_frontpage.py
```

## License

MIT (`SPDX-License-Identifier: MIT`).
