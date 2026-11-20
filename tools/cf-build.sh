#!/bin/sh
# Build the folder Cloudflare serves at https://simonsoliloquy.com/linkshot/ (see wrangler.jsonc).
# Cloudflare's GitHub build runs this and then `npx wrangler deploy` on every push to main.
# By hand: sh tools/cf-build.sh && npx wrangler@4.40.0 deploy
# Only what index.html loads goes in: the page, featured.json (fallback list of featured articles)
# and the sound effects (sfx/manifest.json + sfx/*.mp3); not sfx/raw, tools/, screenshots/ or README.
set -e
cd "$(dirname "$0")/.."
rm -rf .cf && mkdir -p .cf/linkshot
mkdir -p .cf/linkshot/sfx
cp index.html featured.json .cf/linkshot/
cp sfx/manifest.json sfx/*.mp3 .cf/linkshot/sfx/
find .cf -type f | sort
