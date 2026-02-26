import json
import os
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from openai import AzureOpenAI
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips

load_dotenv()

gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

dalle_client = AzureOpenAI(
    api_key=os.getenv("AZURE_DALLE_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_DALLE_ENDPOINT"),
)


def load_timestamps(json_file: str) -> list[dict]:
    with open(json_file) as f:
        return json.load(f)


def get_transcript(words: list[dict]) -> str:
    return " ".join(w["word"] for w in words)


def generate_scenes(words: list[dict], audio_duration: float, interval: float = 2.0) -> list[dict]:
    """Use GPT-4o to generate one scene prompt every `interval` seconds."""
    import math
    n_scenes = math.ceil(audio_duration / interval)
    scenes = []
    for i in range(n_scenes):
        start = round(i * interval, 2)
        end = round(min((i + 1) * interval, audio_duration), 2)
        # Get the actual words spoken during this scene
        spoken = " ".join(
            w["word"] for w in words
            if w["start"] < end and w["end"] > start
        )
        scenes.append({"start": start, "end": end, "spoken": spoken, "prompt": None})

    # Ask GPT-4o for a prompt per scene based on what's actually being said
    scene_descriptions = "\n".join(
        f"Scene {i+1} [{s['start']}s-{s['end']}s]: words spoken = \"{s['spoken']}\""
        for i, s in enumerate(scenes)
    )
    response = gpt_client.chat.completions.create(
        model=GPT_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a video director creating a vertical short-form video (9:16, like Instagram Reels). "
                    "For each scene, you are given the exact Hinglish words being spoken. "
                    "Generate a vivid, cinematic DALL-E 3 image prompt that DIRECTLY and LITERALLY illustrates "
                    "what is being said in that scene. Do not be generic — match the specific words. "
                    "Return JSON with a 'prompts' key containing an array of strings, one per scene."
                ),
            },
            {
                "role": "user",
                "content": f"Scenes with spoken words:\n{scene_descriptions}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    prompts = json.loads(response.choices[0].message.content)["prompts"]
    for i, scene in enumerate(scenes):
        scene["prompt"] = prompts[i]
        print(f"  Scene {i+1} [{scene['start']}s-{scene['end']}s] \"{scene['spoken']}\" → {scene['prompt'][:80]}...")
    return scenes


def generate_image(prompt: str, output_path: str):
    """Generate an image using DALL-E 3 and save it."""
    response = dalle_client.images.generate(
        model=DALLE_DEPLOYMENT,
        prompt=prompt,
        size="1024x1792",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    urllib.request.urlretrieve(image_url, output_path)
    print(f"  Saved image: {output_path}")


GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")
DALLE_DEPLOYMENT = os.getenv("AZURE_DALLE_DEPLOYMENT")
FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)


def draw_caption(base_img: np.ndarray, text: str) -> np.ndarray:
    """Draw a caption with semi-transparent background on the image using PIL."""
    W, H = 1024, 1792
    img = Image.fromarray(base_img).convert("RGBA")

    # Measure text size
    dummy = ImageDraw.Draw(img)
    bbox = dummy.textbbox((0, 0), text, font=FONT)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x, pad_y = 40, 24
    bar_h = text_h + pad_y * 2
    bar_y = H // 2 + 20  # just below center

    # Semi-transparent dark bar
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, bar_y, W, bar_y + bar_h], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img, overlay)

    # Draw text centered on bar
    draw = ImageDraw.Draw(img)
    x = (W - text_w) // 2
    y = bar_y + pad_y
    # Shadow
    draw.text((x + 3, y + 3), text, font=FONT, fill=(0, 0, 0, 200))
    # Main text in yellow for visibility
    draw.text((x, y), text, font=FONT, fill=(255, 230, 0, 255))

    return np.array(img.convert("RGB"))


def build_video(scenes: list[dict], words: list[dict], audio_file: str, output_file: str, images_dir: str):
    """Stitch images + captions + audio into a video."""
    audio = AudioFileClip(audio_file)
    clips = []

    for i, scene in enumerate(scenes):
        img_path = os.path.join(images_dir, f"scene_{i:02d}.png")
        base_img = np.array(Image.open(img_path).resize((1024, 1792)).convert("RGB"))
        duration = scene["end"] - scene["start"]

        # Words in this scene
        scene_words = [
            w for w in words
            if w["start"] < scene["end"] and w["end"] > scene["start"]
        ]

        def make_frame(t, base=base_img, sw=scene_words, s=scene):
            abs_t = s["start"] + t
            current = next(
                (w for w in sw if w["start"] <= abs_t < w["end"]),
                None
            )
            if current:
                text = current["word"].strip(".,।").upper()
                return draw_caption(base, text)
            return base

        clip = VideoClip(make_frame, duration=duration)
        clips.append(clip)

    final = concatenate_videoclips(clips).with_audio(audio)
    final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    print(f"\nVideo saved to: {output_file}")


if __name__ == "__main__":
    audio_file = "/Users/ankitgupta/Downloads/audio.mpeg"
    timestamps_file = "/Users/ankitgupta/Downloads/audio_timestamps_hinglish.json"
    images_dir = "/Users/ankitgupta/Downloads/video_images"
    output_file = "/Users/ankitgupta/Downloads/output_video.mp4"

    os.makedirs(images_dir, exist_ok=True)

    print("Loading timestamps...")
    words = load_timestamps(timestamps_file)
    transcript = get_transcript(words)
    audio_duration = words[-1]["end"]

    print("Generating scenes with GPT-4o...")
    scenes = generate_scenes(words, audio_duration)
    print(f"\nGot {len(scenes)} scenes.")

    print("\nGenerating images with DALL-E 3...")
    for i, scene in enumerate(scenes):
        img_path = os.path.join(images_dir, f"scene_{i:02d}.png")
        if not os.path.exists(img_path):
            print(f"  Generating scene {i+1}...")
            generate_image(scene["prompt"], img_path)
        else:
            print(f"  Scene {i+1} already exists, skipping.")

    print("\nBuilding video...")
    build_video(scenes, words, audio_file, output_file, images_dir)
