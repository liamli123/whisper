#!/usr/bin/env python3
"""
Merge grammar-book output files into a lesson JSON as "grammarPoints".

Usage: python merge_grammar.py <lesson.json> <gout_dir>

Each gout_dir/gout*.json is an array of
{"pattern", "connection", "meaning", "explanation", "examples"}.
Entries are keyed by pattern. Reports any pattern used in the segments
that has no grammar-book entry.
"""

import json
import sys
from pathlib import Path

ENTRY_KEYS = {"pattern", "connection", "meaning", "explanation", "examples"}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    lesson_path = Path(sys.argv[1])
    gout_dir = Path(sys.argv[2])

    lesson = json.loads(lesson_path.read_text(encoding="utf-8"))

    points = {}
    problems = []
    for f in sorted(gout_dir.glob("gout*.json")):
        try:
            entries = json.loads(f.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            problems.append(f"{f.name}: invalid JSON ({e})")
            continue
        for e in entries:
            if not ENTRY_KEYS <= set(e):
                problems.append(f"{f.name}: entry missing keys: {e.get('pattern', '?')}")
                continue
            points[e["pattern"]] = {
                "connection": e["connection"],
                "meaning": e["meaning"],
                "explanation": e["explanation"],
                "examples": e["examples"],
            }

    used = {g["pattern"] for s in lesson["segments"] for g in s.get("grammar", [])}
    missing = sorted(used - set(points))

    lesson["grammarPoints"] = points
    lesson_path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    print(f"Grammar book: {len(points)} entries merged into {lesson_path}")
    if missing:
        print(f"MISSING entries for {len(missing)} patterns: {missing}")
    for p in problems:
        print(f"PROBLEM: {p}")
    sys.exit(1 if (missing or problems) else 0)


if __name__ == "__main__":
    main()
