#!/usr/bin/env python3
"""
Convert a youtube.py transcript (.md) into a lesson JSON for the learn
site, and register it in site/data/index.json.

After building the skeleton (timestamps + Japanese sentences), it launches
Claude Code headlessly to fill in the analysis for every segment:
Chinese translation, vocabulary (hiragana/romaji/Chinese) and grammar notes.

Usage: python make_lesson.py <transcript.md> [--no-analyze]
"""

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SITE_DATA = Path(__file__).parent / "site" / "data"

ANALYSIS_PROMPT = """\
You are annotating a Japanese lesson for a Chinese-speaking Japanese learner.

The lesson JSON is at: {lesson_path}
Its "segments" array holds objects {{"t", "sec", "jp", "zh", "vocab", "grammar"}}
where zh/vocab/grammar are currently empty. The sentences are consecutive
fragments of the video "{title}".

Fill in, for EVERY segment:
- "zh": natural Simplified Chinese translation of the fragment
- "vocab": array of {{"word", "reading", "romaji", "zh"}} — the words worth
  learning (nouns, verbs, adjectives, adverbs, set expressions), 1-6 items.
  reading = kana (hiragana; katakana for loanwords), romaji = pronunciation,
  zh = Simplified Chinese meaning. Skip bare particles and ultra-basic words
  (です/ます/これ) unless the fragment has nothing else.
- "grammar": array of {{"pattern", "zh"}} — 0-3 grammar patterns or
  conversational set phrases used in the fragment (e.g. 〜てしまう, 〜ですもん),
  each with a brief Simplified Chinese explanation of its role in this
  sentence. Empty array is fine for trivial fragments.

For trivial fragments — backchannel/filler responses (そうですね, 確かに,
なるほど, うん) and other very short utterances that a learner doesn't need
explained — fill in "zh" but leave "vocab" and "grammar" as empty arrays.

THEN build the lesson's grammar book ("grammarPoints", a top-level object
keyed by pattern string). For every UNIQUE pattern that appears in any
segment's grammar array, write a teacher-style entry the way a Japanese
language school teacher would teach that point:
{{"connection": "<接续规则: what forms it attaches to>",
  "meaning": "<核心含义, one clear sentence>",
  "explanation": "<详细讲解, 3-6 sentences: nuance, spoken/written register,
   typical situations, and contrast with an easily-confused similar pattern;
   for casual contractions give the full form (〜ちゃう = 〜てしまう)>",
  "examples": [{{"jp": "...", "zh": "..."}}, {{"jp": "...", "zh": "..."}}]
   — first the sentence from the video, then one new simple example}}

How to do it efficiently:
1. Split the segments into chunks of ~35 and launch parallel background
   agents, one per chunk. Give each agent its chunk (index i + jp text),
   the rules above, and have it write a JSON array of
   {{"i", "zh", "vocab", "grammar"}} to its own output file in a temp dir.
2. Merge with: python "{merge_script}" "{lesson_path}" <temp_out_dir>
   It reports how many segments were filled and lists any missing indices.
3. If any segments are missing or any output file was invalid, re-run just
   those and merge again. Continue only when the merge reports ALL segments
   filled with no problems.
4. Extract the unique grammar patterns, chunk them ~28 per agent, and fan
   out teacher-entry agents the same way (each writes gout<NN>.json).
5. Merge with: python "{grammar_merge_script}" "{lesson_path}" <temp_gout_dir>
   Re-run any missing patterns until it reports none missing.

Do not modify any file other than the lesson JSON and your temp files.
When done, reply with one line:
filled <n>/<total> segments, <m> grammar points.
"""


def run_claude_analysis(lesson_path: Path, title: str) -> bool:
    claude = shutil.which("claude")
    if not claude:
        print("Claude Code CLI not found on PATH - skipping analysis.")
        return False

    prompt = ANALYSIS_PROMPT.format(
        lesson_path=lesson_path,
        title=title,
        merge_script=Path(__file__).parent / "merge_analysis.py",
        grammar_merge_script=Path(__file__).parent / "merge_grammar.py",
    )

    print("Launching Claude Code to analyze the lesson...")
    print("(this typically takes a few minutes - progress is quiet until done)")
    # Flags go first and the prompt is piped via stdin: the npm .cmd shim
    # re-parses the command line, and a multi-line prompt in argv can
    # swallow any flags that come after it.
    subprocess.run(
        [claude, "-p",
         "--permission-mode", "acceptEdits",
         "--allowedTools", "Read,Edit,Write,Glob,Bash(python:*)"],
        input=prompt,
        encoding="utf-8",
        cwd=Path(__file__).parent,
    )

    # Trust the file, not the exit code: analysis succeeded only if every
    # segment got a translation and every grammar pattern got a book entry.
    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    unfilled = sum(1 for s in lesson["segments"] if not s.get("zh"))
    if unfilled:
        print(f"{unfilled}/{len(lesson['segments'])} segments still unfilled.")
        return False
    used = {g["pattern"] for s in lesson["segments"] for g in s.get("grammar", [])}
    missing = used - set(lesson.get("grammarPoints", {}))
    if missing:
        print(f"{len(missing)} grammar patterns have no grammar-book entry.")
        return False
    return True


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug or "lesson"


def normalize_jp(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[^0-9A-Za-z぀-ヿ一-鿿]", "", s).lower()


def keep_segment(jp: str, kept_norms: list) -> bool:
    """Drop trivial fillers (そうですね, 確かに...) and sentences whose
    meaning already appeared (videos often preview/recap soundbites)."""
    n = normalize_jp(jp)
    if len(n) <= 6:
        return False
    if any(difflib.SequenceMatcher(None, n, k).ratio() >= 0.85
           for k in kept_norms):
        return False
    kept_norms.append(n)
    return True


def to_seconds(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


def parse_transcript(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")

    title_m = re.search(r"^# (.+)$", text, re.M)
    title = title_m.group(1).strip() if title_m else md_path.stem

    def meta(name: str) -> str:
        m = re.search(rf"- \*\*{name}\*\*: (.+)", text)
        return m.group(1).strip() if m else ""

    source = meta("Source")
    video_id_m = re.search(r"[?&]v=([\w-]{11})", source)
    video_id = video_id_m.group(1) if video_id_m else ""

    segments = []
    kept_norms = []
    for m in re.finditer(r"^\*\*\[(\d+:\d{2}(?::\d{2})?)\]\*\* (.+)$", text, re.M):
        ts, jp = m.group(1), m.group(2).strip()
        if not keep_segment(jp, kept_norms):
            continue
        segments.append({
            "t": ts,
            "sec": to_seconds(ts),
            "jp": jp,
            "zh": "",
            "vocab": [],   # {"word", "reading", "romaji", "zh"}
            "grammar": [],  # {"pattern", "zh"}
        })

    return {
        "id": slugify(title),
        "title": title,
        "source": source,
        "videoId": video_id,
        "channel": meta("Channel"),
        "duration": meta("Duration"),
        "segments": segments,
    }


def update_index(lesson: dict):
    index_path = SITE_DATA / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    index = [e for e in index if e["id"] != lesson["id"]]
    index.append({
        "id": lesson["id"],
        "title": lesson["title"],
        "channel": lesson["channel"],
        "duration": lesson["duration"],
        "segmentCount": len(lesson["segments"]),
    })
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Build a lesson from a youtube.py transcript and "
                    "auto-fill the analysis with Claude Code.")
    parser.add_argument("transcript", help="Transcript .md produced by youtube.py / ytt")
    parser.add_argument("--no-analyze", action="store_true",
                        help="Only build the skeleton; skip the Claude Code analysis")
    args = parser.parse_args()

    md_path = Path(args.transcript)
    if not md_path.exists():
        print(f"Transcript not found: {md_path}")
        sys.exit(1)

    lesson = parse_transcript(md_path)
    if not lesson["segments"]:
        print("No timestamped segments found in the transcript.")
        sys.exit(1)

    SITE_DATA.mkdir(parents=True, exist_ok=True)
    out_path = SITE_DATA / f"{lesson['id']}.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        if any(s.get("zh") for s in existing.get("segments", [])):
            print(f"Lesson already exists WITH analysis: {out_path}")
            print("Delete that file first if you really want to rebuild it.")
            sys.exit(1)
    out_path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")
    update_index(lesson)

    print(f"Lesson skeleton written: {out_path}")
    print(f"Segments: {len(lesson['segments'])}")

    if args.no_analyze:
        print("Skipping analysis (--no-analyze). Ask Claude Code to fill in "
              "zh/vocab/grammar, or rerun without --no-analyze.")
        return

    if run_claude_analysis(out_path, lesson["title"]):
        print(f"Lesson ready: {out_path}")
        print("Deploy with: cd learn/site && vercel --prod --yes")
    else:
        print("Analysis did not complete - the skeleton is saved; "
              "ask Claude Code to fill it in, or rerun make_lesson.py.")
        sys.exit(1)


if __name__ == "__main__":
    main()
