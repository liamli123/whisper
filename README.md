# Whisper Audio Transcription Tool - User Instructions

## Overview
This project provides multiple Python scripts for transcribing audio files using OpenAI's Whisper and faster-whisper models. It's specifically optimized for Japanese language transcription but supports multiple languages.

## Prerequisites

### Required Libraries
```bash
pip install openai-whisper
pip install faster-whisper
```

### System Requirements
- Python 3.7+
- CUDA-compatible GPU (optional, for faster processing)
- Audio files in supported formats (mp3, wav, m4a, etc.)

---

## Quick Start (Recommended)

### **execute.py** - Interactive Transcription Tool

**The easiest way to transcribe audio files!** No code editing required.

**Usage**:
```bash
python execute.py <audio_file>
```

**Examples**:
```bash
python execute.py audio.mp3
python execute.py recording.wav
python execute.py interview.m4a
```

**What it does**:
1. Checks your audio file
2. Shows available Whisper models with details
3. Lets you choose a model
4. Lets you select language (or auto-detect)
5. Lets you choose transcription mode:
   - **Basic**: Simple transcription
   - **Formatted**: Advanced sentence detection (best for Japanese)
   - **Enhanced**: Word-level timestamps
6. Processes your audio and saves results

**Output files** (automatically named based on your input):
- `<filename>_transcription.txt` - Basic transcription
- `<filename>_formatted.txt` - Formatted transcription
- `<filename>_detailed.txt` - Detailed with timestamps

**Features**:
- No code editing needed
- Interactive menu system
- Colored terminal output for easy reading
- Automatic output file naming
- Progress information
- Error handling

---

## Available Scripts

### 1. **control.py** - Model Explorer
**Purpose**: Lists all available Whisper models

**Usage**:
```bash
python Whisper/control.py
```

**Output**: Displays available model names (tiny, base, small, medium, large, large-v2, large-v3, etc.)

---

### 2. **transcribe.py** - Basic Transcription
**Purpose**: Simple transcription script for quick audio-to-text conversion

**Features**:
- Uses large-v3 model
- Optimized for Japanese language
- Splits text by Japanese commas (、)
- Saves output to text file

**Usage**:
1. Place your audio file (e.g., `1.mp3`) in the project directory
2. Run the script:
   ```bash
   python Whisper/transcribe.py
   ```

**Configuration**:
- **Audio file**: Change line 5 - `result = model.transcribe("1.mp3", language="ja")`
- **Language**: Modify `language="ja"` (use "en" for English, "zh" for Chinese, etc.)
- **Output file**: Change line 12 - `with open("output.txt", "w", encoding="utf-8")`

**Output**: Creates `output.txt` with transcribed text, one sentence per line

---

### 3. **format_transcribe.py** - Advanced Formatting
**Purpose**: Transcription with intelligent sentence detection and formatting for Japanese

**Features**:
- Detects Japanese sentence boundaries
- Recognizes common Japanese endings (ます, です, した, etc.)
- Adds proper punctuation
- Normalizes Unicode characters
- Returns structured output with statistics

**Usage**:
1. Update the audio filename in the script (line 91)
2. Run:
   ```bash
   python Whisper/format_transcribe.py
   ```

**Configuration**:
```python
processor = TranscriptProcessor()
result = processor.process_audio(
    audio_file="2.mp3",        # Your audio file
    output_file="formatted_output.txt",  # Output file
    language="ja"              # Language code
)
```

**Output**:
- `formatted_output.txt` - Properly formatted transcript
- Console output showing formatted text and sentence count

**Programmatic Usage**:
```python
from format_transcribe import TranscriptProcessor

processor = TranscriptProcessor()
result = processor.process_audio("audio.mp3", "output.txt")

print(f"Raw text: {result['raw_text']}")
print(f"Formatted text: {result['formatted_text']}")
print(f"Sentence count: {result['sentence_count']}")
```

---

### 4. **transcribe_enhanced.py** - Detailed Transcription with Timestamps
**Purpose**: High-performance transcription with word-level timestamps and VAD filtering

**Features**:
- Uses faster-whisper for improved performance
- Word-level timestamps
- Voice Activity Detection (VAD) to filter silence
- GPU acceleration (when available)
- Creates two output files: simple and detailed

**Usage**:
1. Update the audio filename (line 13)
2. Run:
   ```bash
   python Whisper/transcribe_enhanced.py
   ```

**Configuration**:
```python
# Line 13: Change audio file
audio_file = "1.mp3"

# Lines 16-22: Modify transcription parameters
segments, info = model.transcribe(
    audio_file,
    language="ja",  # Language code
    word_timestamps=True,  # Enable/disable word timestamps
    vad_filter=True,  # Enable/disable VAD
    vad_parameters=dict(min_silence_duration_ms=500)  # Silence threshold
)
```

**Output Files**:
1. `output.txt` - Simple full transcript
2. `output_detailed.txt` - Detailed transcript with:
   - Segment timestamps
   - Word-level timestamps
   - Language detection confidence
   - Total duration
   - Word count

---

## Model Selection Guide

| Model | Size | Speed | Accuracy | VRAM Required |
|-------|------|-------|----------|---------------|
| tiny | 39M | Fastest | Good | ~1GB |
| base | 74M | Very Fast | Better | ~1GB |
| small | 244M | Fast | Good | ~2GB |
| medium | 769M | Moderate | Very Good | ~5GB |
| large-v3 | 1550M | Slower | Excellent | ~10GB |

**To change model**: Update line 3 in transcribe.py or line 9 in format_transcribe.py:
```python
model = whisper.load_model("medium")  # Use any model name
```

---

## Language Codes

Common language codes for transcription:
- `ja` - Japanese
- `en` - English
- `zh` - Chinese
- `ko` - Korean
- `es` - Spanish
- `fr` - French
- `de` - German
- `ru` - Russian

For auto-detection, omit the `language` parameter.

---

## Tips for Best Results

1. **Audio Quality**: Use clear audio with minimal background noise
2. **GPU Usage**: For faster processing, ensure CUDA is installed and available
3. **Model Selection**:
   - Use `large-v3` for best accuracy
   - Use `medium` or `small` for faster processing
   - Use `tiny` for real-time applications
4. **Japanese Text**: Use `format_transcribe.py` for better sentence formatting
5. **Timestamps**: Use `transcribe_enhanced.py` when you need precise timing information
6. **VAD Filtering**: Adjust `min_silence_duration_ms` to control silence filtering sensitivity

---

## Troubleshooting

### Out of Memory Error
- Use a smaller model (medium, small, or base)
- Process shorter audio files
- Disable CUDA: Set `device="cpu"` in transcribe_enhanced.py (line 5)

### Poor Transcription Quality
- Ensure audio is clear and properly recorded
- Try using large-v3 model
- Specify the correct language code
- Check audio file format compatibility

### Slow Processing
- Use faster-whisper (transcribe_enhanced.py)
- Enable GPU acceleration
- Use a smaller model
- Process shorter segments

### Import Errors
```bash
# Install required packages
pip install openai-whisper
pip install faster-whisper
pip install torch  # For GPU support
```

---

## Quick Start Examples

### Using execute.py (Recommended)

**Most Common Use Case**:
```bash
# Simply run with your audio file
python execute.py myaudio.mp3

# Then follow the interactive prompts:
# 1. Choose a model (e.g., 7 for large-v3)
# 2. Select language (e.g., 2 for Japanese)
# 3. Pick mode (e.g., 2 for Formatted)
```

**For English Audio**:
```bash
python execute.py podcast.mp3
# Choose: medium model, English, Basic mode
```

**For Japanese with Timestamps**:
```bash
python execute.py interview.mp3
# Choose: large-v3 model, Japanese, Enhanced mode
```

### Using Individual Scripts (Manual)

1. **Check available models**:
   ```bash
   python Whisper/control.py
   ```

2. **Quick transcription**:
   ```bash
   # Edit transcribe.py line 5 with your audio file
   python Whisper/transcribe.py
   ```

3. **Advanced with formatting**:
   ```bash
   # Edit format_transcribe.py line 91 with your audio file
   python Whisper/format_transcribe.py
   ```

4. **Full-featured with timestamps**:
   ```bash
   # Edit transcribe_enhanced.py line 13 with your audio file
   python Whisper/transcribe_enhanced.py
   ```

---

## File Structure

```
Whisper/
├── execute.py              # Interactive tool (RECOMMENDED)
├── control.py              # List available models
├── transcribe.py           # Basic transcription
├── format_transcribe.py    # Formatted transcription (Japanese)
└── transcribe_enhanced.py  # Enhanced with timestamps
```

---

## Support

For issues or questions about:
- **Whisper model**: https://github.com/openai/whisper
- **Faster-whisper**: https://github.com/guillaumekln/faster-whisper
- **This project**: Check the script comments or modify parameters as needed
