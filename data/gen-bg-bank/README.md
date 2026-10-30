# Generator background bank

This directory holds **14 pre-generated 16:9 AI backgrounds**, named `bank-01.webp` through `bank-14.webp`.

`scripts/make_gen_bg.py` uses one when the morning routine has no `--image` file and no live image API. It picks the oldest unused file (`entries.<file>.added` in `used.json`, then the filename). After every file has been used, it reuses the least-recently-used one (`last_used`, then `uses`). A git checkout does not preserve file modification times, so the order lives in `used.json` rather than on the files.

These files are real AI images. Do not add code-drawn, procedural, or placeholder art.

Seeded on 2026-10-30:

| File | Source |
| --- | --- |
| bank-01.webp … bank-10.webp | Real daily backgrounds from `assets/gen-bg-archive/` and the same images after they rotated out of the 7-day archive (2026-10-16 through 2026-10-25). Code-drawn days (2026-10-26 through 2026-10-30) are not included. |
| bank-11.webp … bank-14.webp | New 16:9 cosmic abstracts generated for the open slots (aurora, neural river, amethyst ring, synaptic light). No text, no people. |

To add or replace a slot, drop in another real 16:9 AI webp under the same name.
