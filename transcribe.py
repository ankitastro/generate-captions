import json
import os
import sys
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")
GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")

gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)


def transcribe_with_word_timestamps(audio_file: str) -> list[dict]:
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "hi-IN"
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    words = []
    done = False

    def on_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            detail = json.loads(evt.result.json)
            for word in detail.get("NBest", [{}])[0].get("Words", []):
                words.append({
                    "word": word["Word"],
                    "start": word["Offset"] / 10_000_000,
                    "end": (word["Offset"] + word["Duration"]) / 10_000_000,
                })

    def on_stopped(evt):
        nonlocal done
        done = True

    recognizer.recognized.connect(on_result)
    recognizer.session_stopped.connect(on_stopped)
    recognizer.canceled.connect(on_stopped)

    recognizer.start_continuous_recognition()
    while not done:
        pass
    recognizer.stop_continuous_recognition()

    return words


def to_hinglish(words: list[dict]) -> list[dict]:
    devanagari_words = [w["word"] for w in words]

    response = gpt_client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Hinglish transliterator. "
                    "Convert each Hindi word from Devanagari to natural Roman script Hinglish "
                    "(the way people type Hindi casually on WhatsApp). "
                    "Keep English words as-is. "
                    'Return JSON as {"words": [...]} with one string per input word.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(devanagari_words, ensure_ascii=False),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    result = json.loads(response.choices[0].message.content)["words"]
    if len(result) < len(devanagari_words):
        result += devanagari_words[len(result):]
    hinglish_words = result[:len(devanagari_words)]
    return [
        {"word": hinglish_words[i], "start": w["start"], "end": w["end"]}
        for i, w in enumerate(words)
    ]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        sys.exit(1)

    audio_file = sys.argv[1]
    base = audio_file.rsplit(".", 1)[0]

    print("Transcribing with Azure Speech SDK...")
    words = transcribe_with_word_timestamps(audio_file)

    print("Converting to Hinglish...")
    hinglish_words = to_hinglish(words)

    print(f"\n{'Word':<25} {'Start (s)':>10} {'End (s)':>10}")
    print("-" * 47)
    for w in hinglish_words:
        print(f"{w['word']:<25} {w['start']:>10.3f} {w['end']:>10.3f}")

    devanagari_file = base + "_timestamps.json"
    hinglish_file = base + "_timestamps_hinglish.json"

    with open(devanagari_file, "w") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)

    with open(hinglish_file, "w") as f:
        json.dump(hinglish_words, f, indent=2, ensure_ascii=False)

    print(f"\nSaved Devanagari → {devanagari_file}")
    print(f"Saved Hinglish   → {hinglish_file}")
