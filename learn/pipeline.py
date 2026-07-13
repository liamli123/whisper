#!/usr/bin/env python3
"""
One-command pipeline: YouTube URL -> deployed lesson.

Runs the full chain:
  1. youtube.py      - download audio + Whisper transcript
  2. make_lesson.py  - lesson JSON + Claude analysis
  3. make_clips.py   - per-sentence audio clips
  4. git commit + push (Vercel auto-deploys)

Usage: ytl <youtube_url> [--no-push]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent          # E:\Websites\Whisper
LEARN = Path(__file__).parent
WORKDIR = ROOT / "downloads"                 # gitignored; mp3 + .md land here


def run(cmd, **kw):
    print(f"\n=== {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kw)


def newest(pattern: str, exclude=()) -> Path:
    files = [f for f in WORKDIR.glob(pattern) if f.name not in exclude]
    if not files:
        sys.exit(f"Expected a {pattern} file in {WORKDIR} - pipeline step failed?")
    return max(files, key=lambda f: f.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube URL -> transcribed, analyzed, clipped, deployed lesson.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--no-push", action="store_true",
                        help="Do everything except git commit/push")
    args = parser.parse_args()

    WORKDIR.mkdir(exist_ok=True)

    # 1. Transcribe (audio + markdown land in downloads/)
    run([sys.executable, str(ROOT / "youtube.py"), args.url, "-o", str(WORKDIR)])
    md = newest("*.md")
    mp3 = newest("*.mp3")
    print(f"Transcript: {md.name}\nAudio: {mp3.name}")

    # 2. Build lesson + Claude analysis (exits non-zero if analysis incomplete)
    run([sys.executable, str(LEARN / "make_lesson.py"), str(md)])
    lesson = max(
        (f for f in (LEARN / "site" / "data").glob("*.json")
         if f.name != "index.json"),
        key=lambda f: f.stat().st_mtime)
    print(f"Lesson: {lesson.name}")

    # 3. Cut per-sentence clips
    run([sys.executable, str(LEARN / "make_clips.py"), str(lesson), str(mp3)])

    # 4. Deploy via git push (Vercel watches master)
    if args.no_push:
        print("\nSkipping push (--no-push). Deploy with: git add learn/site "
              "&& git commit && git push")
        return
    run(["git", "add", "learn/site"], cwd=ROOT)
    run(["git", "commit", "-m", f"Add lesson: {lesson.stem}"], cwd=ROOT)
    run(["git", "push", "origin", "master"], cwd=ROOT)
    print(f"\nDone. Live in ~30s at: "
          f"https://japanese-learn-two.vercel.app/lesson.html?id={lesson.stem}")


if __name__ == "__main__":
    main()
