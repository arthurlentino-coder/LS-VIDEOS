import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="pt")
    args = parser.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        args.input,
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )

    output_segments = []
    flat_words = []
    for segment in segments:
        words = []
        for word in segment.words or []:
            item = {
                "id": f"w{len(flat_words)}",
                "text": word.word.strip(),
                "start": round(float(word.start), 3),
                "end": round(float(word.end), 3),
                "probability": round(float(word.probability), 4),
            }
            if item["text"]:
                words.append(item)
                flat_words.append(item)
        output_segments.append({
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": segment.text.strip(),
            "words": words,
        })

    payload = {
        "language": info.language,
        "languageProbability": round(float(info.language_probability), 4),
        "duration": round(float(info.duration), 3),
        "segments": output_segments,
        "words": flat_words,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{target}: {len(output_segments)} segmentos, {len(flat_words)} palavras")


if __name__ == "__main__":
    main()
