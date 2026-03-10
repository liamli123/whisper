#!/usr/bin/env python3
"""
Interactive Whisper Transcription Tool
Usage: python execute.py <audio_file>
Example: python execute.py audio.mp3
"""

import sys
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import whisper
import re
from typing import List, Dict
import unicodedata

# ANSI color codes for better terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}[INFO]{Colors.END} {text}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {text}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")


def get_user_choice(prompt, options):
    """Get user choice from a list of options"""
    while True:
        try:
            choice = input(f"{Colors.YELLOW}{prompt}{Colors.END} ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num - 1
            else:
                print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)


def select_model():
    """Display available models and let user choose"""
    models = whisper.available_models()

    print_header("AVAILABLE WHISPER MODELS")

    # Model information
    model_info = {
        'tiny': '39M params, ~1GB VRAM, Fastest, Good accuracy',
        'base': '74M params, ~1GB VRAM, Very fast, Better accuracy',
        'small': '244M params, ~2GB VRAM, Fast, Good accuracy',
        'medium': '769M params, ~5GB VRAM, Moderate speed, Very good accuracy',
        'large': '1550M params, ~10GB VRAM, Slower, Excellent accuracy',
        'large-v2': '1550M params, ~10GB VRAM, Slower, Excellent accuracy (v2)',
        'large-v3': '1550M params, ~10GB VRAM, Slower, Best accuracy (v3)',
    }

    for i, model in enumerate(models, 1):
        info = model_info.get(model, 'Model information not available')
        print(f"{Colors.BOLD}{i}.{Colors.END} {Colors.GREEN}{model:<12}{Colors.END} - {info}")

    choice_idx = get_user_choice("\nSelect model number:", models)
    selected_model = models[choice_idx]
    print_success(f"Selected model: {selected_model}")
    return selected_model


def select_language():
    """Let user select or auto-detect language"""
    print_header("LANGUAGE SELECTION")

    languages = {
        '1': ('Auto-detect', None),
        '2': ('Japanese', 'ja'),
        '3': ('English', 'en'),
        '4': ('Chinese', 'zh'),
        '5': ('Korean', 'ko'),
        '6': ('Spanish', 'es'),
        '7': ('French', 'fr'),
        '8': ('German', 'de'),
        '9': ('Russian', 'ru'),
    }

    for key, (name, code) in languages.items():
        print(f"{Colors.BOLD}{key}.{Colors.END} {name}")

    while True:
        choice = input(f"{Colors.YELLOW}\nSelect language number: {Colors.END}").strip()
        if choice in languages:
            lang_name, lang_code = languages[choice]
            print_success(f"Selected language: {lang_name}")
            return lang_code
        else:
            print_error("Please enter a valid number (1-9)")


def select_transcription_mode():
    """Let user select transcription mode"""
    print_header("TRANSCRIPTION MODE")

    modes = [
        ("Basic", "Simple transcription, split by sentences"),
        ("Formatted (Japanese)", "Advanced formatting with sentence detection (best for Japanese)"),
        ("Enhanced with Timestamps", "Detailed transcription with word-level timestamps (requires faster-whisper)"),
    ]

    for i, (name, desc) in enumerate(modes, 1):
        print(f"{Colors.BOLD}{i}.{Colors.END} {Colors.GREEN}{name}{Colors.END}")
        print(f"   {Colors.CYAN}{desc}{Colors.END}")

    choice_idx = get_user_choice("\nSelect mode number:", modes)
    print_success(f"Selected mode: {modes[choice_idx][0]}")
    return choice_idx + 1


def basic_transcribe(audio_file, model_name, language):
    """Basic transcription mode"""
    print_info(f"Loading model: {model_name}...")
    model = whisper.load_model(model_name)
    model.half = False

    print_info(f"Transcribing audio file: {audio_file}...")
    result = model.transcribe(audio_file, language=language) if language else model.transcribe(audio_file)
    text = result["text"]

    # Split sentences
    sentences = text.split("、") if language == "ja" else text.split(". ")

    # Create output filename
    base_name = os.path.splitext(audio_file)[0]
    output_file = f"{base_name}_transcription.txt"

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        for sentence in sentences:
            if sentence.strip():
                f.write(sentence.strip() + "\n")

    print_success(f"Transcription saved to: {output_file}")

    # Display preview
    print(f"\n{Colors.BOLD}Preview:{Colors.END}")
    for i, sentence in enumerate(sentences[:5], 1):
        if sentence.strip():
            print(f"{i}. {sentence.strip()}")
    if len(sentences) > 5:
        print(f"... and {len(sentences) - 5} more sentences")


class TranscriptProcessor:
    """Advanced transcript processor for Japanese text"""

    def __init__(self, model_name):
        self.model = whisper.load_model(model_name)
        self.model.half = False
        self.sentence_endings = [
            'ます', 'です', 'した', 'ません',
            'ございます', 'でしょう', 'だ', 'である',
            'のだ', 'んだ', 'わ', 'よ', 'ね'
        ]

    def detect_sentence_boundaries(self, text: str) -> List[str]:
        """Split text into sentences using multiple Japanese sentence markers."""
        segments = re.split('[。！？\n]', text)
        sentences = []

        for segment in segments:
            if not segment.strip():
                continue

            found_ending = False
            for ending in self.sentence_endings:
                parts = segment.split(ending)
                if len(parts) > 1:
                    for part in parts[:-1]:
                        if part.strip():
                            sentences.append(f"{part.strip()}{ending}")
                    if parts[-1].strip():
                        sentences.append(parts[-1].strip())
                    found_ending = True
                    break

            if not found_ending and segment.strip():
                sentences.append(segment.strip())

        return sentences

    def format_transcript(self, sentences: List[str]) -> str:
        """Format the transcript with proper spacing and punctuation."""
        formatted_text = ""
        for sentence in sentences:
            sentence = re.sub(r'([、。！？])', r'\1 ', sentence)
            sentence = unicodedata.normalize('NFKC', sentence)

            if not sentence.strip().endswith(('。', '！', '？')):
                sentence += '。'

            formatted_text += sentence + '\n'

        return formatted_text

    def process_audio(self, audio_file: str, language: str = "ja") -> Dict:
        """Process audio file and return formatted transcript."""
        result = self.model.transcribe(audio_file, language=language) if language else self.model.transcribe(audio_file)
        raw_text = result["text"]

        sentences = self.detect_sentence_boundaries(raw_text)
        formatted_transcript = self.format_transcript(sentences)

        return {
            "raw_text": raw_text,
            "formatted_text": formatted_transcript,
            "sentence_count": len(sentences)
        }


def formatted_transcribe(audio_file, model_name, language):
    """Formatted transcription mode"""
    print_info(f"Loading model: {model_name}...")
    processor = TranscriptProcessor(model_name)

    print_info(f"Transcribing and formatting audio file: {audio_file}...")
    result = processor.process_audio(audio_file, language=language)

    # Create output filename
    base_name = os.path.splitext(audio_file)[0]
    output_file = f"{base_name}_formatted.txt"

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result["formatted_text"])

    print_success(f"Formatted transcription saved to: {output_file}")
    print_info(f"Total sentences: {result['sentence_count']}")

    # Display preview
    print(f"\n{Colors.BOLD}Preview:{Colors.END}")
    lines = result["formatted_text"].split('\n')
    for i, line in enumerate(lines[:5], 1):
        if line.strip():
            print(f"{i}. {line.strip()}")
    if len(lines) > 5:
        print(f"... and {len(lines) - 5} more lines")


def enhanced_transcribe(audio_file, model_name, language):
    """Enhanced transcription with timestamps using faster-whisper"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print_error("faster-whisper is not installed!")
        print_info("Install it with: pip install faster-whisper")
        return

    print_info(f"Loading model: {model_name}...")
    device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print_info(f"Model loaded on {device} using {compute_type} precision")

    print_info(f"Transcribing audio file with timestamps: {audio_file}...")

    segments, info = model.transcribe(
        audio_file,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    ) if language else model.transcribe(
        audio_file,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    # Create output filenames
    base_name = os.path.splitext(audio_file)[0]
    output_simple = f"{base_name}_transcription.txt"
    output_detailed = f"{base_name}_detailed.txt"

    # Process segments
    full_text = ""
    words_with_timestamps = []
    segment_list = list(segments)

    with open(output_simple, "w", encoding="utf-8") as f_text, \
         open(output_detailed, "w", encoding="utf-8") as f_detailed:

        f_detailed.write("# Detailed Transcription with Timestamps\n\n")

        for segment in segment_list:
            full_text += segment.text + " "

            f_detailed.write(f"## Segment [{segment.start:.2f}s -> {segment.end:.2f}s]\n")
            f_detailed.write(f"{segment.text}\n\n")

            if hasattr(segment, 'words') and segment.words:
                f_detailed.write("### Words:\n")
                for word in segment.words:
                    word_info = f"  - {word.word} ({word.start:.2f}s -> {word.end:.2f}s)"
                    f_detailed.write(word_info + "\n")
                    words_with_timestamps.append((word.word, word.start, word.end))
                f_detailed.write("\n")

        f_text.write(full_text)

        f_detailed.write("\n## Summary\n")
        f_detailed.write(f"- **Language**: {info.language} (confidence: {info.language_probability:.2%})\n")
        f_detailed.write(f"- **Duration**: {segment_list[-1].end if segment_list else 0:.2f} seconds\n")
        f_detailed.write(f"- **Word Count**: {len(words_with_timestamps)}\n")

    print_success(f"Simple transcription saved to: {output_simple}")
    print_success(f"Detailed transcription saved to: {output_detailed}")
    print_info(f"Detected language: {info.language} ({info.language_probability:.2%} confidence)")
    print_info(f"Total words: {len(words_with_timestamps)}")

    # Display preview
    print(f"\n{Colors.BOLD}Preview (first 3 segments):{Colors.END}")
    for i, segment in enumerate(segment_list[:3], 1):
        print(f"{i}. [{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    if len(segment_list) > 3:
        print(f"... and {len(segment_list) - 3} more segments")


def main():
    """Main execution function"""
    print_header("WHISPER AUDIO TRANSCRIPTION TOOL")

    # Check if audio file is provided
    if len(sys.argv) < 2:
        print_error("No audio file specified!")
        print(f"\n{Colors.BOLD}Usage:{Colors.END}")
        print(f"  python execute.py <audio_file>")
        print(f"\n{Colors.BOLD}Example:{Colors.END}")
        print(f"  python execute.py audio.mp3")
        print(f"  python execute.py recording.wav")
        sys.exit(1)

    audio_file = sys.argv[1]

    # Check if file exists
    if not os.path.exists(audio_file):
        print_error(f"Audio file not found: {audio_file}")
        sys.exit(1)

    file_size = os.path.getsize(audio_file) / (1024 * 1024)  # Size in MB
    print_info(f"Audio file: {audio_file}")
    print_info(f"File size: {file_size:.2f} MB")

    # Interactive selections
    model_name = select_model()
    language = select_language()
    mode = select_transcription_mode()

    print_header("PROCESSING")

    try:
        if mode == 1:
            basic_transcribe(audio_file, model_name, language)
        elif mode == 2:
            formatted_transcribe(audio_file, model_name, language)
        elif mode == 3:
            enhanced_transcribe(audio_file, model_name, language)

        print_header("COMPLETED")
        print_success("Transcription completed successfully!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
