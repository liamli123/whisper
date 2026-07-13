#!/usr/bin/env python3
"""
YouTube Audio Transcription Tool
Downloads a YouTube video's audio with yt-dlp and transcribes it
with Whisper (Japanese by default), saving a Markdown transcript.

Usage: python youtube.py <youtube_url> [--model MODEL] [--language ja] [--delete-audio]
Example: python youtube.py https://www.youtube.com/watch?v=XXXXXXXXXXX
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from execute import (
    Colors,
    TranscriptProcessor,
    print_header,
    print_info,
    print_success,
    print_error,
)

def download_audio(url: str, out_dir: Path) -> tuple[Path, dict]:
    """Download the audio track of a YouTube video as mp3. Returns (path, video info)."""
    try:
        import yt_dlp
    except ImportError:
        print_error("yt-dlp is not installed! Install it with: pip install yt-dlp")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    print_info(f"Downloading audio from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = Path(ydl.prepare_filename(info)).with_suffix(".mp3")

    if not audio_path.exists():
        print_error(f"Expected audio file not found: {audio_path}")
        sys.exit(1)

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    print_success(f"Audio downloaded: {audio_path.name} ({size_mb:.2f} MB)")
    return audio_path, info


def format_timestamp(seconds: float) -> str:
    """Format seconds as [HH:MM:SS] or [MM:SS]."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def write_markdown(output_file: Path, info: dict, result: dict,
                   segments: list, model_name: str, language: str):
    """Write the transcript as a Markdown file."""
    duration = info.get("duration") or (segments[-1]["end"] if segments else 0)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# {info.get('title', 'Transcript')}\n\n")
        f.write(f"- **Source**: {info.get('webpage_url', '')}\n")
        f.write(f"- **Channel**: {info.get('uploader', 'Unknown')}\n")
        f.write(f"- **Duration**: {format_timestamp(duration)}\n")
        f.write(f"- **Model**: {model_name}\n")
        f.write(f"- **Language**: {language}\n")
        f.write(f"- **Transcribed**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## 文字起こし（タイムスタンプ付き）\n\n")
        for seg in segments:
            text = seg["text"].strip()
            if text:
                f.write(f"**[{format_timestamp(seg['start'])}]** {text}\n\n")

        f.write("## 全文\n\n")
        f.write(result["formatted_text"])


def main():
    parser = argparse.ArgumentParser(
        description="Download a YouTube video's audio and transcribe it to Markdown."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--model", default="large-v3",
                        help="Whisper model to use (default: large-v3)")
    parser.add_argument("-l", "--language", default="ja",
                        help="Language code, e.g. ja, en, zh, ko (default: ja)")
    parser.add_argument("--delete-audio", action="store_true",
                        help="Delete the downloaded audio file after transcription")
    parser.add_argument("-o", "--output-dir", default=".",
                        help="Folder to save the audio and transcript "
                             "(default: current folder)")
    args = parser.parse_args()

    print_header("YOUTUBE AUDIO TRANSCRIPTION")

    audio_path, info = download_audio(args.url, Path(args.output_dir).resolve())

    print_info(f"Loading model: {args.model}...")
    processor = TranscriptProcessor(args.model)

    duration = info.get("duration")
    if duration:
        print_info(f"Audio duration: {format_timestamp(duration)}")
    print_info(f"Transcribing ({args.language}): {audio_path.name}...")
    # verbose=False enables whisper's tqdm progress bar (percentage + ETA;
    # 100 frames = 1 second of audio)
    whisper_result = processor.model.transcribe(
        str(audio_path), language=args.language, verbose=False
    )
    segments = whisper_result.get("segments", [])

    if args.language == "ja":
        sentences = processor.detect_sentence_boundaries(whisper_result["text"])
        result = {
            "formatted_text": processor.format_transcript(sentences),
            "sentence_count": len(sentences),
        }
    else:
        result = {
            "formatted_text": whisper_result["text"].strip() + "\n",
            "sentence_count": len(segments),
        }

    output_file = audio_path.with_suffix(".md")
    write_markdown(output_file, info, result, segments, args.model, args.language)

    print_success(f"Markdown transcript saved to: {output_file}")
    print_info(f"Total sentences: {result['sentence_count']}")

    if args.delete_audio:
        audio_path.unlink()
        print_info(f"Deleted downloaded audio: {audio_path.name}")
    else:
        print_info(f"Audio kept at: {audio_path}")

    # Preview
    print(f"\n{Colors.BOLD}Preview (first 5 segments):{Colors.END}")
    for i, seg in enumerate(segments[:5], 1):
        print(f"{i}. [{format_timestamp(seg['start'])}] {seg['text'].strip()}")
    if len(segments) > 5:
        print(f"... and {len(segments) - 5} more segments")

    print_header("COMPLETED")


if __name__ == "__main__":
    main()
