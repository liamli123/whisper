# Whisper Transcription Project

This project uses OpenAI's Whisper speech recognition models to transcribe audio files, with a focus on Japanese language transcription.

## Updates on Whisper Models

The project has been updated with information about the latest Whisper models and features. Please see [whisper_update.md](whisper_update.md) for a comprehensive overview of:

- Current state of Whisper models
- New features and capabilities
- Recommendations for this project

## Files in this Project

- **transcribe.py**: Original basic transcription script using OpenAI's Whisper
- **transcribe_enhanced.py**: New enhanced version using Faster-Whisper with additional features
- **format_transcribe.py**: Advanced transcription with Japanese-specific formatting
- **control.py**: Utility script to list available Whisper models
- **whisper_update.md**: Detailed information about the latest Whisper developments

## Enhanced Transcription Features

The new `transcribe_enhanced.py` script includes several improvements:

1. **Faster processing** using the Faster-Whisper implementation
2. **Word-level timestamps** for precise audio alignment
3. **Voice Activity Detection (VAD)** to filter out non-speech parts
4. **Automatic hardware detection** (CUDA GPU or CPU)
5. **Detailed output** with timestamps and summary information

## Installation

To use the enhanced version, you'll need to install the faster-whisper package:

```bash
pip install faster-whisper
```

For GPU support, you'll also need to install CUDA and cuDNN appropriate for your system.

## Usage

### Basic Transcription

```bash
python transcribe.py
```

### Enhanced Transcription with Timestamps

```bash
python transcribe_enhanced.py
```

This will create two output files:
- `output.txt`: Simple transcription text
- `output_detailed.txt`: Detailed transcription with timestamps and word-level information

### Advanced Formatting for Japanese

```python
from format_transcribe import TranscriptProcessor

processor = TranscriptProcessor()
result = processor.process_audio(
    audio_file="your_audio.mp3",
    output_file="formatted_output.txt"
)
```

## Customization

You can modify the scripts to:
- Change the input audio file
- Select a different Whisper model
- Adjust language settings
- Configure VAD parameters
- Customize output formats

## Requirements

- Python 3.7+
- OpenAI Whisper or Faster-Whisper
- FFmpeg (for audio processing)