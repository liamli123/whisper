# learn — Japanese Learning Site

Turns transcripts produced by `youtube.py` / `ytt` into an interactive
Japanese learning site (vocabulary with hiragana/romaji/Chinese meanings,
grammar notes, and tap-to-play YouTube timestamps), deployed on Vercel.

## Structure

```
learn/
├── make_lesson.py      # transcript .md -> lesson JSON skeleton
├── merge_analysis.py   # merge chunked analysis back into the lesson JSON
├── make_clips.py       # cut per-sentence audio clips (word-aligned)
└── site/               # static site (deploy this folder to Vercel)
    ├── index.html      # lesson list
    ├── lesson.html     # lesson view (sentence cards + embedded player)
    ├── style.css
    ├── audio/<id>/     # one mp3 clip per sentence
    └── data/
        ├── index.json  # lesson index
        └── <id>.json   # one file per lesson
```

## Adding a new lesson

1. Transcribe a video: `ytt "https://www.youtube.com/watch?v=..."`
2. Build the lesson: `python E:\Websites\Whisper\learn\make_lesson.py "<video title>.md"`
   — this creates the skeleton AND auto-launches Claude Code headlessly
   (the analysis prompt is built into the script) to fill in translations,
   vocab, and grammar for every segment. Takes a few minutes.
   Use `--no-analyze` to build only the skeleton.
3. Cut per-sentence audio clips (needs the video's mp3 and `pip install pykakasi`):
   `python learn/make_clips.py learn/site/data/<id>.json <audio.mp3>`
   — re-transcribes with word-level timestamps (cached in `<audio>.words.json`)
   and snaps each clip to real sentence boundaries. Segments get a `"clip"`
   field; the site shows a ▶ button on cards that have one.
4. Deploy: push to GitHub (Vercel auto-deploys) or `cd learn/site && vercel --prod --yes`

make_lesson.py refuses to overwrite a lesson that already has analysis —
delete its JSON from `site/data/` first if you want to rebuild one.

## Lesson JSON format

```json
{
  "id": "slug", "title": "...", "videoId": "YouTube ID",
  "segments": [{
    "t": "01:23", "sec": 83,
    "jp": "日本語の文",
    "zh": "中文翻译",
    "vocab": [{"word": "単語", "reading": "たんご", "romaji": "tango", "zh": "单词"}],
    "grammar": [{"pattern": "〜てしまう", "zh": "表示遗憾/完成"}]
  }],
  "grammarPoints": {
    "〜てしまう": {
      "connection": "动词て形＋しまう",
      "meaning": "表示动作彻底完成，或带有遗憾、不由自主的语气",
      "explanation": "详细讲解：语气、场景、与相似句型的区别……",
      "examples": [{"jp": "...", "zh": "..."}, {"jp": "...", "zh": "..."}]
    }
  }
}
```

Each segment's grammar list shows the pattern + its role in that sentence;
tapping it expands the full teacher-style entry from `grammarPoints`
(接续 / 含义 / 讲解 / 例句).

## Site features

- Mobile-first; works well on a phone browser
- Embedded YouTube player: tap any timestamp to jump to that moment
- 隐藏中文 toggle: blurs all Chinese translations for self-testing
  (tap a blurred line to reveal it)
- Light/dark theme follows system preference
