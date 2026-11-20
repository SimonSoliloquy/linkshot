# Linkshot

A 3D slingshot game built from Wikipedia: each level is a whole article laid out as a staircase of its own words. Play at https://simonsoliloquy.com/linkshot/ (the old address https://wiki-linkshot.vercel.app forwards there until about 2026-12-19).

- `index.html`: the whole game (three.js + cannon-es, loaded from a CDN).
- `featured.json`: saved copy of Wikipedia:Featured articles, used only if the live list can't be fetched. Refresh with `python3 tools/featured_list.py`.
- `sfx/`: sound effects (`sfx/raw` holds the sources, not deployed).
- `tools/`: helper scripts, plus the old Supabase leaderboard SQL (history; the leaderboard is now a Cloudflare Worker, `LB.url` in `index.html`).

## Publishing

The game is plain files on Cloudflare (no Worker code runs), served at `simonsoliloquy.com/linkshot/` by the routes in `wrangler.jsonc`. `tools/cf-build.sh` copies only the files the live site needs into `.cf/linkshot/` (the URL path is the folder path). On every push to `main`, Cloudflare's GitHub build runs `sh tools/cf-build.sh` and then `npx wrangler deploy`. By hand: `sh tools/cf-build.sh && npx wrangler@4.40.0 deploy`.

`vercel.json` now only redirects the old Vercel address (project `wiki-linkshot`) to the new one; it can go once the redirect is no longer needed.
