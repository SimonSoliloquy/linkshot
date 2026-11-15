# Linkshot

A 3D slingshot game built from Wikipedia: each level is a whole article laid out as a staircase of its own words. Play at https://wiki-linkshot.vercel.app.

- `index.html`: the whole game (three.js + cannon-es, loaded from a CDN).
- `featured.json`: saved copy of Wikipedia:Featured articles, used only if the live list can't be fetched. Refresh with `python3 tools/featured_list.py`.
- `sfx/`: sound effects (`sfx/raw` holds the sources, not deployed).
- `tools/`: leaderboard SQL (Supabase) and helper scripts.

Pushing to `main` deploys to production on Vercel (project `wiki-linkshot`).
