import whisper
import re
from typing import List, Dict
import unicodedata


class TranscriptProcessor:
    def __init__(self):
        self.model = whisper.load_model("large-v3")
        self.model.half = False

        # Common Japanese sentence endings
        self.sentence_endings = [
            'ます', 'です', 'した', 'ません',
            'ございます', 'でしょう', 'だ', 'である',
            'のだ', 'んだ', 'わ', 'よ', 'ね'
        ]

    def detect_sentence_boundaries(self, text: str) -> List[str]:
        """Split text into sentences using multiple Japanese sentence markers."""
        # First split by obvious markers
        segments = re.split('[。！？\n]', text)

        # Further process each segment
        sentences = []
        for segment in segments:
            if not segment.strip():
                continue

            # Check for sentence endings in the middle of segments
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
            # Add proper spacing after punctuation
            sentence = re.sub(r'([、。！？])', r'\1 ', sentence)

            # Normalize unicode characters
            sentence = unicodedata.normalize('NFKC', sentence)

            # Add proper ending punctuation if missing
            if not sentence.strip().endswith(('。', '！', '？')):
                sentence += '。'

            formatted_text += sentence + '\n'

        return formatted_text

    def process_audio(self, audio_file: str, output_file: str, language: str = "ja") -> Dict:
        """Process audio file and save formatted transcript."""
        # Transcribe audio
        result = self.model.transcribe(audio_file, language=language)
        raw_text = result["text"]

        # Process the transcript
        sentences = self.detect_sentence_boundaries(raw_text)
        formatted_transcript = self.format_transcript(sentences)

        # Save to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_transcript)

        return {
            "raw_text": raw_text,
            "formatted_text": formatted_transcript,
            "sentence_count": len(sentences)
        }


# Example usage
if __name__ == "__main__":
    processor = TranscriptProcessor()
    result = processor.process_audio(
        audio_file="2.mp3",
        output_file="formatted_output.txt"
    )

    print("Processed transcript:")
    print(result["formatted_text"])
    print(f"\nTotal sentences: {result['sentence_count']}")