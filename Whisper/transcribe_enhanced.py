import os
from faster_whisper import WhisperModel

# Check if CUDA is available, otherwise use CPU
device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

# Load the model - using the same large-v3 model but with the faster implementation
model = WhisperModel("large-v3", device=device, compute_type=compute_type)
print(f"Model loaded on {device} using {compute_type} precision")

# Transcribe with word-level timestamps
audio_file = "../1.mp3"
print(f"Transcribing {audio_file}...")

segments, info = model.transcribe(
    audio_file, 
    language="ja",  # Japanese language
    word_timestamps=True,  # Enable word-level timestamps
    vad_filter=True,  # Filter out non-speech parts
    vad_parameters=dict(min_silence_duration_ms=500)  # Adjust VAD parameters
)

# Process the results
full_text = ""
words_with_timestamps = []

# Open files for writing
with open("output.txt", "w", encoding="utf-8") as f_text, \
     open("output_detailed.txt", "w", encoding="utf-8") as f_detailed:
    
    # Write header for detailed output
    f_detailed.write("# Detailed Transcription with Timestamps\n\n")
    
    # Process each segment
    for segment in segments:
        # Write segment to console
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        
        # Add to full text
        full_text += segment.text + " "
        
        # Write segment to detailed file
        f_detailed.write(f"## Segment [{segment.start:.2f}s -> {segment.end:.2f}s]\n")
        f_detailed.write(f"{segment.text}\n\n")
        
        # Process word-level information if available
        if hasattr(segment, 'words') and segment.words:
            f_detailed.write("### Words:\n")
            for word in segment.words:
                word_info = f"  - {word.word} ({word.start:.2f}s -> {word.end:.2f}s)"
                f_detailed.write(word_info + "\n")
                words_with_timestamps.append((word.word, word.start, word.end))
            f_detailed.write("\n")
    
    # Write the full text to the simple output file
    f_text.write(full_text)
    
    # Add summary information
    f_detailed.write("\n## Summary\n")
    f_detailed.write(f"- **Language**: {info.language} (detected: {info.language_probability:.2%})\n")
    f_detailed.write(f"- **Duration**: {sum(segment.end - segment.start for segment in segments):.2f} seconds\n")
    f_detailed.write(f"- **Word Count**: {len(words_with_timestamps)}\n")

print(f"\nTranscription complete!")
print(f"- Basic output saved to: output.txt")
print(f"- Detailed output with timestamps saved to: output_detailed.txt")