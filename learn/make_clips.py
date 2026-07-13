#!/usr/bin/env python3
"""
Cut per-sentence audio clips for a lesson JSON.

The lesson JSON only stores whole-second timestamps (truncated), so cutting
at those marks starts clips up to a second inside the previous sentence.
This script re-transcribes the audio with word-level timestamps, snaps each
segment's start to the actual first-word boundary (matching the segment text
against the word stream), cuts one mp3 per segment with ffmpeg, and writes
the "clip" field back into the lesson JSON.

Usage: python make_clips.py <lesson.json> <audio.mp3> [--model small]
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

SITE = Path(__file__).parent / "site"

START_PAD = 0.10   # seconds before the matched first word
END_PAD = 0.25     # trailing breath after the last word, capped at next start
MATCH_WINDOW = (-0.25, 1.35)  # search for the first word around the marked sec
MIN_SCORE = 0.5    # below this, fall back to "first word at/after sec"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[^0-9A-Za-z぀-ヿ一-鿿]", "", s).lower()


def transcribe_words(audio: Path, model_name: str, cache: Path) -> list:
    if cache.exists():
        print(f"Using cached word timestamps: {cache}")
        return json.loads(cache.read_text(encoding="utf-8"))

    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    import whisper

    print(f"Loading whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    print("Transcribing with word timestamps (this takes a few minutes)...")
    result = model.transcribe(str(audio), language="ja",
                              word_timestamps=True, verbose=False)
    words = [
        {"start": round(w["start"], 3), "end": round(w["end"], 3), "text": w["word"]}
        for seg in result["segments"] for w in seg.get("words", [])
    ]
    cache.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    print(f"{len(words)} words; cached to {cache}")
    return words


def match_start(words: list, sec: int, jp: str) -> float:
    """Find the precise start of the sentence whose truncated timestamp is sec."""
    target = norm(jp)[:6]
    lo, hi = sec + MATCH_WINDOW[0], sec + MATCH_WINDOW[1]
    best_start, best_score = None, -1.0
    for j, w in enumerate(words):
        if w["start"] < lo:
            continue
        if w["start"] > hi:
            break
        cand = norm("".join(x["text"] for x in words[j:j + 6]))[:6]
        score = difflib.SequenceMatcher(None, target, cand).ratio()
        if score > best_score:
            best_start, best_score = w["start"], score
    if best_start is not None and best_score >= MIN_SCORE:
        return best_start
    # Fallback: first word starting at or after the marked second
    for w in words:
        if w["start"] >= sec:
            return w["start"]
    return float(sec)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson", help="Lesson JSON in site/data/")
    parser.add_argument("audio", help="Source audio (mp3/m4a/wav) of the video")
    parser.add_argument("--model", default="small",
                        help="Whisper model for boundary alignment (default: small)")
    args = parser.parse_args()

    lesson_path = Path(args.lesson)
    audio = Path(args.audio)
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    segs = lesson["segments"]

    cache = audio.with_suffix(".words.json")
    words = transcribe_words(audio, args.model, cache)
    if not words:
        sys.exit("No words returned by whisper.")

    starts = [match_start(words, s["sec"], s["jp"]) for s in segs]
    # Keep starts monotonic: a bad match never rewinds before the previous one
    for i in range(1, len(starts)):
        if starts[i] <= starts[i - 1]:
            starts[i] = max(starts[i - 1] + 0.05, float(segs[i]["sec"]))

    audio_end = words[-1]["end"] + 1.0
    clip_dir = SITE / "audio" / lesson["id"]
    clip_dir.mkdir(parents=True, exist_ok=True)

    # Decode the source once; cutting hundreds of clips from wav is
    # sample-accurate and fast, unlike seeking in mp3.
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "src.wav"
        print("Decoding source audio to wav...")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(audio), str(wav)],
                       check=True)

        for i, seg in enumerate(segs):
            nxt = starts[i + 1] if i + 1 < len(segs) else audio_end
            # Walk the words of this sentence; stop at the first long speech
            # gap so clips don't swallow music/b-roll interludes before the
            # next transcribed sentence.
            last_end = None
            for w in words:
                if not (starts[i] <= w["start"] < nxt):
                    continue
                if last_end is not None and w["start"] - last_end > 1.2:
                    break
                last_end = w["end"]
            if last_end is None:
                last_end = nxt
            begin = max(0.0, starts[i] - START_PAD)
            end = min(nxt - 0.02, last_end + END_PAD)
            # Untranscribed speech (e.g. non-Japanese interview portions)
            # defeats the gap check above; cap by how long the sentence
            # could plausibly take to say.
            end = min(end, begin + max(2.0, 0.3 * len(norm(seg["jp"])) + 1.5))
            if end - begin < 0.3:
                end = begin + 0.3
            out = clip_dir / f"{i:03d}.mp3"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(wav),
                 "-ss", f"{begin:.3f}", "-to", f"{end:.3f}",
                 "-b:a", "128k", str(out)],
                check=True)
            seg["clip"] = f"audio/{lesson['id']}/{i:03d}.mp3"
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(segs)} clips cut")

    lesson_path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    total_kb = sum(f.stat().st_size for f in clip_dir.glob("*.mp3")) // 1024
    print(f"Done: {len(segs)} clips in {clip_dir} ({total_kb / 1024:.1f} MB); "
          f"lesson JSON updated.")


if __name__ == "__main__":
    main()
