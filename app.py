import json
import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI
from caption_video import extract_audio, transcribe, add_captions

load_dotenv()

GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")

gpt_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)


def convert_words(words: list[dict], mode: str) -> list[dict]:
    """Convert Devanagari words to Hinglish or English using GPT-4o (batched)."""
    if mode == "Hindi":
        return words

    system_prompt = (
        "You are a Hinglish transliterator. Convert each Hindi word from Devanagari to natural "
        "Roman script Hinglish (the way people type Hindi casually on WhatsApp). Keep English words as-is. "
    ) if mode == "Hinglish" else (
        "You are a translator. Translate each Hindi word from Devanagari to its English equivalent. "
        "For single words, give the best single English word or short phrase. "
    )

    converted = []
    batch_size = 50
    for i in range(0, len(words), batch_size):
        batch = [w["word"] for w in words[i:i + batch_size]]
        response = gpt_client.chat.completions.create(
            model=GPT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt + ' Return JSON as {"words": [...]}'},
                {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        converted.extend(json.loads(response.choices[0].message.content)["words"])

    return [
        {"word": converted[i], "start": w["start"], "end": w["end"]}
        for i, w in enumerate(words)
    ]


# ── Streamlit UI ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Video Caption Dashboard", layout="wide")
st.title("Video Caption Dashboard")

# Persistent temp dir across reruns — recreate if OS cleaned it up
if "tmpdir" not in st.session_state or not os.path.exists(st.session_state["tmpdir"]):
    st.session_state["tmpdir"] = tempfile.mkdtemp()
    st.session_state.pop("video_path", None)
    st.session_state.pop("words", None)

tmpdir = st.session_state["tmpdir"]

uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"])

if uploaded:
    video_path = os.path.join(tmpdir, uploaded.name)
    with open(video_path, "wb") as f:
        f.write(uploaded.read())
    st.session_state["video_path"] = video_path

if "video_path" in st.session_state:
    st.video(st.session_state["video_path"])

    caption_mode = st.radio(
        "Caption language",
        ["Hinglish", "Hindi", "English"],
        horizontal=True,
    )

    if st.button("Transcribe & Generate Captions"):
        with st.spinner("Extracting audio..."):
            wav_path = extract_audio(st.session_state["video_path"])
        with st.spinner("Transcribing..."):
            hindi_words = transcribe(wav_path)
        with st.spinner(f"Converting to {caption_mode}..."):
            words = convert_words(hindi_words, caption_mode)
        st.session_state["words"] = words

    if "words" in st.session_state:
        st.subheader("Transcription — edit if needed")
        edited = st.data_editor(
            st.session_state["words"],
            column_config={
                "word": st.column_config.TextColumn("Word"),
                "start": st.column_config.NumberColumn("Start (s)", format="%.3f"),
                "end": st.column_config.NumberColumn("End (s)", format="%.3f"),
            },
            use_container_width=True,
            num_rows="dynamic",
        )

        if st.button("Burn Captions into Video"):
            output_path = os.path.join(tmpdir, "captioned.mp4")
            with st.spinner("Rendering video... this may take a minute"):
                add_captions(st.session_state["video_path"], edited, output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Captioned Video",
                    data=f,
                    file_name=f"{uploaded.name.rsplit('.', 1)[0]}_captioned.mp4",
                    mime="video/mp4",
                )
