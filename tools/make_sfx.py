#!/usr/bin/env python3
"""Make Linkshot's sound effects with Google's Lyria model (Gemini API).

Run once on your own machine. The key is read from the GEMINI_API_KEY
environment variable and is never written to disk or printed.

    python3 tools/make_sfx.py            # make any sounds that are missing
    python3 tools/make_sfx.py --check    # only say whether the key is set
    python3 tools/make_sfx.py --force    # regenerate everything
    python3 tools/make_sfx.py hop wall   # regenerate just these
    python3 tools/make_sfx.py --recut    # re-trim the clips already in sfx/raw, without calling Google

Clips made another way (for example locally with ComfyUI) can be dropped into
sfx/raw/ as NAME.flac, NAME.wav or NAME.mp3 and trimmed with --recut.

Lyria's clip model always returns 30 seconds of audio, so each prompt asks for
the sound right at the start. The script then cuts out that first sound, fades
it, levels it, and saves a small mono MP3 in sfx/. The untrimmed originals are
kept in sfx/raw/ (not deployed) so a sound can be re-cut without paying again.
"""
import base64, json, os, re, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, RAW = ROOT / "sfx", ROOT / "sfx" / "raw"
URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "lyria-3-clip-preview"
TAIL = " The sound happens once, immediately at the very start, followed by silence. No music, no melody, no rhythm, no vocals, no background."

# name: (seconds to keep, prompt)
SOUNDS = {
    "hop":    (0.18, "Sound effect: one very short, soft, dry wooden tick, like a small ball tapping a wooden block."),
    "boing":  (0.45, "Sound effect: one bright cartoon spring boing, rising in pitch."),
    "fling":  (0.40, "Sound effect: one quick elastic slingshot release, a rubber band twang with a short whoosh."),
    "caught": (0.35, "Sound effect: one soft low thud, a small ball landing on felt in a wooden tray."),
    "wall":   (0.70, "Sound effect: one big rubbery trampoline bounce, a deep springy boing."),
    "side":   (0.25, "Sound effect: one light glassy tink, a marble tapping a glass pane."),
    "link":   (0.90, "Sound effect: one short magical teleport shimmer, a bright rising sparkle chime."),
    "fall":   (0.90, "Sound effect: one short descending slide whistle, a cartoon falling sound."),
    "win":    (2.20, "Sound effect: one short triumphant fanfare of four rising notes on bright mallets and brass, ending cleanly."),
}


def generate(name, prompt, key):
    body = json.dumps({"model": MODEL, "input": prompt + TAIL}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "Api-Revision": "2026-05-20", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"{name}: Google answered {e.code}. {detail}")
    for step in data.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for block in step.get("content", []):
            if block.get("type") == "audio" and block.get("data"):
                return base64.b64decode(block["data"])
    raise SystemExit(f"{name}: the response had no audio in it: {json.dumps(data)[:300]}")


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], capture_output=True, text=True)


def find_raw(name):
    """The untrimmed clip for a sound, whatever made it (Lyria MP3, or a FLAC/WAV made locally with ComfyUI)."""
    for ext in ("flac", "wav", "mp3"):
        if (RAW / f"{name}.{ext}").exists():
            return RAW / f"{name}.{ext}"
    return RAW / f"{name}.mp3"


def cut(name, seconds):
    """Keep the first sound in the raw clip: strip leading silence, trim, fade out, level to -1.5 dB peak."""
    raw, tmp, out = find_raw(name), RAW / f"{name}.cut.wav", OUT / f"{name}.mp3"
    fade = min(0.08, seconds / 3)
    chain = (f"silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.005,"
             f"atrim=0:{seconds},afade=t=out:st={seconds - fade:.3f}:d={fade:.3f}")
    r = ffmpeg("-i", str(raw), "-af", chain, "-ac", "1", "-ar", "44100", str(tmp))
    if r.returncode != 0:
        raise SystemExit(f"{name}: ffmpeg could not cut the clip.\n{r.stderr[-400:]}")
    probe = ffmpeg("-i", str(tmp), "-af", "volumedetect", "-f", "null", "-")
    m = re.search(r"max_volume: (-?[\d.]+) dB", probe.stderr)
    gain = (-1.5 - float(m.group(1))) if m else 0.0
    gain = max(-20.0, min(30.0, gain))
    r = ffmpeg("-i", str(tmp), "-af", f"volume={gain:.2f}dB", "-ac", "1", "-b:a", "96k", str(out))
    tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(f"{name}: ffmpeg could not write {out.name}.\n{r.stderr[-400:]}")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if "--check" in flags:
        print("GEMINI_API_KEY is set." if key else "GEMINI_API_KEY is not set in this terminal.")
        return 0 if key else 1
    unknown = [a for a in args if a not in SOUNDS]
    if unknown:
        raise SystemExit(f"Unknown sound(s): {', '.join(unknown)}. Choose from: {', '.join(SOUNDS)}")
    names = args or list(SOUNDS)
    force = "--force" in flags or bool(args)
    recut = "--recut" in flags                      # re-trim from sfx/raw without calling Google
    RAW.mkdir(parents=True, exist_ok=True)
    for name in names:
        seconds, prompt = SOUNDS[name]
        raw = find_raw(name)
        if recut or (raw.exists() and not force):
            if not raw.exists():
                print(f"{name}: no raw clip to re-cut, skipped"); continue
        else:
            if not key:
                raise SystemExit("GEMINI_API_KEY is not set. Run:  export GEMINI_API_KEY=your-key   and try again.")
            print(f"{name}: asking Lyria...", flush=True)
            raw.write_bytes(generate(name, prompt, key))
        out = cut(name, seconds)
        print(f"{name}: {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.1f} KB")
    made = sorted(p.stem for p in OUT.glob("*.mp3"))
    (OUT / "manifest.json").write_text(json.dumps({"sounds": made}))
    print(f"manifest: {len(made)} sounds ready: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
