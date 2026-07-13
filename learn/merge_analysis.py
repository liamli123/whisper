#!/usr/bin/env python3
"""
Merge chunked analysis output files into a lesson JSON.

Usage: python merge_analysis.py <lesson.json> <out_dir>

Each out_dir/out*.json is an array of {"i", "zh", "vocab", "grammar"}.
Items are matched to lesson segments by index "i". Reports any segment
left without analysis.
"""

import json
import sys
from pathlib import Path

VOCAB_KEYS = {"word", "reading", "romaji", "zh"}
GRAMMAR_KEYS = {"pattern", "zh"}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    lesson_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])

    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
    segments = lesson["segments"]

    problems = []
    filled = set()
    for f in sorted(out_dir.glob("out*.json")):
        try:
            items = json.loads(f.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            problems.append(f"{f.name}: invalid JSON ({e})")
            continue
        for item in items:
            i = item.get("i")
            if not isinstance(i, int) or not 0 <= i < len(segments):
                problems.append(f"{f.name}: bad index {i!r}")
                continue
            vocab = [v for v in item.get("vocab", []) if VOCAB_KEYS <= set(v)]
            grammar = [g for g in item.get("grammar", []) if GRAMMAR_KEYS <= set(g)]
            segments[i]["zh"] = item.get("zh", "")
            segments[i]["vocab"] = vocab
            segments[i]["grammar"] = grammar
            filled.add(i)

    missing = [i for i in range(len(segments)) if i not in filled]

    lesson_path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    print(f"Merged {len(filled)}/{len(segments)} segments into {lesson_path}")
    if missing:
        print(f"MISSING analysis for indices: {missing}")
    for p in problems:
        print(f"PROBLEM: {p}")
    sys.exit(1 if (missing or problems) else 0)


if __name__ == "__main__":
    main()
