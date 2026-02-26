import json
import os
import sys
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from openai import AzureOpenAI
from moviepy import VideoFileClip, VideoClip

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")
GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")

gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

FONT_LATIN = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_DEVANAGARI = "/System/Library/Fonts/Supplemental/ITFDevanagari.ttc"


def get_font(text: str, size: int) -> ImageFont.FreeTypeFont:
    """Pick Devanagari font if text contains Devanagari characters, else Latin."""
    is_devanagari = any('\u0900' <= ch <= '\u097F' for ch in text)
    path = FONT_DEVANAGARI if is_devanagari else FONT_LATIN
    return ImageFont.truetype(path, size)


def extract_audio(video_file: str) -> str:
    """Extract audio from video as WAV for Azure Speech SDK."""
    wav_file = video_file.rsplit(".", 1)[0] + "_extracted.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", video_file,
        "-ar", "16000", "-ac", "1", "-f", "wav", wav_file
    ], check=True, capture_output=True)
    print(f"Extracted audio → {wav_file}")
    return wav_file


def transcribe(wav_file: str) -> list[dict]:
    """Transcribe audio with Azure Speech SDK (hi-IN) for word-level timestamps."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    speech_config.speech_recognition_language = "hi-IN"
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    audio_config = speechsdk.audio.AudioConfig(filename=wav_file)
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


def to_hinglish(words: list[dict], batch_size: int = 50) -> list[dict]:
    """Convert Devanagari words to natural Hinglish using GPT-4o in batches."""
    system_prompt = (
        "You are a Hinglish transliterator. "
        "Convert each Hindi word from Devanagari to natural Roman script Hinglish "
        "(the way people type Hindi casually on WhatsApp). "
        "Keep English words as-is. "
        "Return only a JSON array of strings, one per input word, in the same order. "
        "No explanation, no extra text."
    )

    hinglish_all = []
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        devanagari_batch = [w["word"] for w in batch]
        response = gpt_client.chat.completions.create(
            model=GPT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt + ' Return JSON as {"words": [...]}'},
                {"role": "user", "content": json.dumps(devanagari_batch, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        result = json.loads(response.choices[0].message.content)["words"]
        if len(result) < len(devanagari_batch):
            result += devanagari_batch[len(result):]
        hinglish_all.extend(result[:len(devanagari_batch)])
        print(f"  Converted words {i+1}–{min(i+batch_size, len(words))}")

    return [
        {"word": hinglish_all[i], "start": w["start"], "end": w["end"]}
        for i, w in enumerate(words)
    ]


def draw_caption(frame: np.ndarray, text: str, size: tuple) -> np.ndarray:
    """Burn caption onto a video frame using PIL."""
    W, H = size
    font_size = max(40, W // 12)
    font = get_font(text, font_size)

    img = Image.fromarray(frame).convert("RGBA")
    dummy = ImageDraw.Draw(img)
    bbox = dummy.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x, pad_y = 40, 20
    bar_h = text_h + pad_y * 2
    bar_y = H // 2 + 20

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, bar_y, W, bar_y + bar_h], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    x = (W - text_w) // 2
    y = bar_y + pad_y
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=(255, 230, 0, 255))

    return np.array(img.convert("RGB"))


def add_captions(video_file: str, words: list[dict], output_file: str, progress_callback=None):
    """Overlay captions on the video."""
    clip = VideoFileClip(video_file)
    W, H = int(clip.w), int(clip.h)
    total_frames = max(int(clip.fps * clip.duration), 1)
    frame_count = [0]

    def make_frame(t):
        frame = clip.get_frame(t)
        frame_count[0] += 1
        if progress_callback:
            progress_callback(min(frame_count[0] / total_frames, 1.0))
        current = next((w for w in words if w["start"] <= t < w["end"]), None)
        if current:
            text = current["word"].strip(".,।").upper()
            return draw_caption(frame, text, (W, H))
        return frame

    captioned = VideoClip(make_frame, duration=clip.duration)
    captioned = captioned.with_audio(clip.audio)
    captioned.write_videofile(output_file, fps=clip.fps, codec="libx264", audio_codec="aac", logger=None)
    print(f"\nCaptioned video saved → {output_file}")


SEGMENT_DURATION = 2.0  # seconds per Ken Burns segment


def add_effects(video_file: str, output_file: str, progress_callback=None):
    """Ken Burns zoom alternating direction every 2 seconds."""
    clip = VideoFileClip(video_file)
    W, H = int(clip.w), int(clip.h)
    total_frames = max(int(clip.fps * clip.duration), 1)
    frame_count = [0]

    def make_frame(t):
        frame = clip.get_frame(t)
        frame_count[0] += 1
        if progress_callback:
            progress_callback(min(frame_count[0] / total_frames, 1.0))
        segment_idx = int(t / SEGMENT_DURATION)
        t_in_seg = t % SEGMENT_DURATION
        zoom_in = (segment_idx % 2 == 0)
        progress = t_in_seg / SEGMENT_DURATION
        scale = 1.0 + 0.08 * (progress if zoom_in else (1 - progress))
        crop_w = int(W / scale)
        crop_h = int(H / scale)
        left = (W - crop_w) // 2
        top = (H - crop_h) // 2
        img = Image.fromarray(frame)
        cropped = img.crop((left, top, left + crop_w, top + crop_h))
        return np.array(cropped.resize((W, H), Image.LANCZOS))

    effected = VideoClip(make_frame, duration=clip.duration).with_audio(clip.audio)
    effected.write_videofile(output_file, fps=clip.fps, codec="libx264", audio_codec="aac", logger=None)
    print(f"\nEffects applied → {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python caption_video.py <video_file>")
        sys.exit(1)

    video_file = sys.argv[1]
    base = video_file.rsplit(".", 1)[0]
    output_file = base + "_captioned.mp4"

    print("Step 1: Extracting audio...")
    wav_file = extract_audio(video_file)

    print("Step 2: Transcribing...")
    words = transcribe(wav_file)

    print("Step 3: Converting to Hinglish...")
    hinglish_words = to_hinglish(words)

    # Save timestamps
    with open(base + "_timestamps_hinglish.json", "w") as f:
        json.dump(hinglish_words, f, indent=2, ensure_ascii=False)
    print(f"Saved timestamps → {base}_timestamps_hinglish.json")

    print("Step 4: Adding captions to video...")
    add_captions(video_file, hinglish_words, output_file)

    # Cleanup extracted audio
    os.remove(wav_file)
