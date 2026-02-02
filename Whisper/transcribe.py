import whisper

model = whisper.load_model("large-v3")
model.half = False
result = model.transcribe("1.mp3", language="ja")  # "ja" for Japanese
text = result["text"]
sentences = text.split("、")  # Split at periods followed by a space
for sentence in sentences:
    print(sentence)

# Open a file for writing (replace "output.txt" with your desired filename)
with open("output.txt", "w", encoding="utf-8") as f:
    for sentence in sentences:
        f.write(sentence + "\n")  # Write each sentence to a new line