import json, os, wave as wav_mod, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from moviepy import VideoFileClip, VideoClip, AudioFileClip, concatenate_videoclips

load_dotenv("/Users/ankitgupta/generate_captions/.env")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION     = os.getenv("AZURE_REGION")

DATE   = "2026-03-01"
ASSETS = "/Users/ankitgupta/rashifal_creator/Rashifal_assets"
FONTS_DIR = "/Users/ankitgupta/generate_captions/fonts"

PART1_NAMES = ["मेष", "वृषभ", "मिथुन", "कर्क", "Leo", "कन्या"]
PART2_NAMES = ["तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]

RASHI_VIDEO = {
    "मेष":   f"{ASSETS}/part_1/aries.mp4",
    "वृषभ":  f"{ASSETS}/part_1/taurus.mp4",
    "मिथुन": f"{ASSETS}/part_1/mithun.mp4",
    "कर्क":  f"{ASSETS}/part_1/cancer.mp4",
    "Leo":   f"{ASSETS}/part_1/leo.mp4",
    "कन्या": f"{ASSETS}/part_1/virgo.mp4",
    "तुला":  f"{ASSETS}/part2/libra.mp4",
    "वृश्चिक":f"{ASSETS}/part2/scorpion.mp4",
    "धनु":   f"{ASSETS}/part2/sagitarius.mp4",
    "मकर":   f"{ASSETS}/part2/capriocpon.mp4",
    "कुंभ":  f"{ASSETS}/part2/aquarius.mp4",
    "मीन":   f"{ASSETS}/part2/pieces.mp4",
}

# Map Azure Devanagari output → canonical rashi name
BOUNDARY_MAP = {
    "मेष":     "मेष",
    "वृषभ":    "वृषभ",
    "मिथुन":   "मिथुन",
    "कर्क":    "कर्क",
    "कन्या":   "कन्या",
    "तुला":    "तुला",
    "वृश्चिक": "वृश्चिक",
    "धनु":     "धनु",
    "मकर":     "मकर",
    "कुंभ":    "कुंभ",
    "मीन":     "मीन",
    # Leo variants Azure might return
    "लियो":  "Leo",
    "लिओ":   "Leo",
    "lio":   "Leo",
    "leo":   "Leo",
    "Leo":   "Leo",
}

WAV1, WAV2 = "/tmp/rashi_p1.wav", "/tmp/rashi_p2.wav"


def wav_duration(path):
    with wav_mod.open(path) as wf:
        return wf.getnframes() / wf.getframerate()


# ── 4. Timestamps ─────────────────────────────────────────────────────────────
def get_timestamps(wav_path):
    sc = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    sc.speech_recognition_language = "hi-IN"
    sc.request_word_level_timestamps()
    sc.output_format = speechsdk.OutputFormat.Detailed
    rec = speechsdk.SpeechRecognizer(
        speech_config=sc,
        audio_config=speechsdk.audio.AudioConfig(filename=wav_path)
    )
    words, done = [], False

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            nbest = json.loads(evt.result.json).get("NBest", [])
            if nbest:  # guard against empty NBest list
                for w in nbest[0].get("Words", []):
                    words.append({
                        "word":  w["Word"],
                        "start": round(w["Offset"] / 10_000_000, 3),
                        "end":   round((w["Offset"] + w["Duration"]) / 10_000_000, 3),
                    })

    def on_stopped(evt):
        nonlocal done
        done = True

    rec.recognized.connect(on_recognized)
    rec.session_stopped.connect(on_stopped)
    rec.canceled.connect(on_stopped)
    rec.start_continuous_recognition()
    while not done:
        time.sleep(0.05)
    rec.stop_continuous_recognition()
    return words


# ── 5. Boundary detection ─────────────────────────────────────────────────────
def detect_boundaries(names, words, total_dur):
    boundaries = {}
    for w in words:
        key = BOUNDARY_MAP.get(w["word"], w["word"])
        if key in names and key not in boundaries:
            boundaries[key] = w["start"]
    boundaries["_end"] = total_dur - 0.1
    return boundaries


# ── 6. Captions ───────────────────────────────────────────────────────────────
def get_font(text, size):
    is_devanagari = any('\u0900' <= ch <= '\u097F' for ch in text)
    if is_devanagari:
        for p in [f"{FONTS_DIR}/ITFDevanagari.ttc",
                  "/System/Library/Fonts/Supplemental/ITFDevanagari.ttc"]:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    for p in [f"{FONTS_DIR}/Arial-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_caption(frame, text, W, H):
    font = get_font(text, max(32, W // 12))
    img  = Image.fromarray(frame).convert("RGBA")
    d    = ImageDraw.Draw(img)
    bb   = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad, bar_y = 16, int(H * 0.80)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, bar_y, W, bar_y + th + pad * 2], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img, ov)
    d2  = ImageDraw.Draw(img)
    x, y = (W - tw) // 2, bar_y + pad
    d2.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 200))
    d2.text((x, y),         text, font=font, fill=(255, 230, 0, 255))
    return np.array(img.convert("RGB"))


# ── 7. Build video ────────────────────────────────────────────────────────────
def build_video(names, words, wav_path, total_dur, out_path):
    boundaries = detect_boundaries(names, words, total_dur)
    detected = [k for k in boundaries if k != "_end"]
    print(f"  Detected: {detected}")
    missing = [n for n in names if n not in boundaries]
    if missing:
        print(f"  WARNING — missing: {missing}")
        # Print nearby words to help debug
        for w in words[:30]:
            print(f"    {w['word']!r} @ {w['start']:.2f}s")

    open_clips, segments = [], []
    for idx, name in enumerate(names):
        if name not in boundaries:
            continue
        seg_start  = boundaries[name]
        next_name  = next((n for n in names[idx + 1:] if n in boundaries), "_end")
        seg_end    = boundaries[next_name]
        seg_dur    = round(seg_end - seg_start, 3)
        print(f"  {name}: {seg_start:.2f}s → {seg_end:.2f}s ({seg_dur:.1f}s)")

        seg_words = [w for w in words if seg_start <= w["start"] < seg_end]
        clip      = VideoFileClip(RASHI_VIDEO[name])
        open_clips.append(clip)
        W, H   = int(clip.w), int(clip.h)
        reps   = int(seg_dur / clip.duration) + 2
        looped = concatenate_videoclips([clip] * reps).subclipped(0, seg_dur)
        open_clips.append(looped)

        def make_frame(t, sw=seg_words, off=seg_start, lp=looped, w=W, h=H):
            frame = lp.get_frame(t)
            cur   = next((x for x in sw if x["start"] <= t + off < x["end"]), None)
            if cur:
                return draw_caption(frame, cur["word"], w, h)
            return frame

        segments.append(VideoClip(make_frame, duration=seg_dur))

    if not segments:
        print("  ERROR: no segments detected, aborting.")
        return

    first_name = next(n for n in names if n in boundaries)
    audio_clip = AudioFileClip(wav_path).subclipped(boundaries[first_name], boundaries["_end"])
    final      = concatenate_videoclips(segments).with_audio(audio_clip)
    final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", logger=None)
    for c in open_clips:
        try:
            c.close()
        except Exception:
            pass
    print(f"  Saved → {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Step 4: Getting timestamps...")
    dur1 = wav_duration(WAV1)
    dur2 = wav_duration(WAV2)
    print(f"  WAV durations — Part1: {dur1:.1f}s | Part2: {dur2:.1f}s")

    words1 = get_timestamps(WAV1)
    print(f"  Part 1: {len(words1)} words recognized")
    words2 = get_timestamps(WAV2)
    print(f"  Part 2: {len(words2)} words recognized")

    print(f"  First 5 words P1: {[w['word'] for w in words1[:5]]}")
    print(f"  First 5 words P2: {[w['word'] for w in words2[:5]]}")

    print("\nStep 5: Building videos...")
    build_video(PART1_NAMES, words1, WAV1, dur1, f"/tmp/rashifal_{DATE}_part1.mp4")
    build_video(PART2_NAMES, words2, WAV2, dur2, f"/tmp/rashifal_{DATE}_part2.mp4")
    print(f"\nDone!\n  /tmp/rashifal_{DATE}_part1.mp4\n  /tmp/rashifal_{DATE}_part2.mp4")
