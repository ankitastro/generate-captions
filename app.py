import hashlib
import json
import os
import sqlite3
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

DB_PATH = os.path.join(os.path.dirname(__file__), "captions.db")


# ── Database ───────────────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            file_hash   TEXT PRIMARY KEY,
            filename    TEXT,
            hindi       TEXT,
            hinglish    TEXT,
            english     TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()


def get_cached(file_hash: str) -> dict | None:
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT hindi, hinglish, english FROM transcriptions WHERE file_hash = ?",
        (file_hash,)
    ).fetchone()
    con.close()
    if row:
        return {
            "Hindi": json.loads(row[0]),
            "Hinglish": json.loads(row[1]),
            "English": json.loads(row[2]),
        }
    return None


def save_cache(file_hash: str, filename: str, data: dict):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT OR REPLACE INTO transcriptions (file_hash, filename, hindi, hinglish, english)
        VALUES (?, ?, ?, ?, ?)
    """, (
        file_hash, filename,
        json.dumps(data["Hindi"], ensure_ascii=False),
        json.dumps(data["Hinglish"], ensure_ascii=False),
        json.dumps(data["English"], ensure_ascii=False),
    ))
    con.commit()
    con.close()


def save_edits(file_hash: str, mode: str, words: list[dict]):
    col = {"Hindi": "hindi", "Hinglish": "hinglish", "English": "english"}[mode]
    con = sqlite3.connect(DB_PATH)
    con.execute(
        f"UPDATE transcriptions SET {col} = ? WHERE file_hash = ?",
        (json.dumps(words, ensure_ascii=False), file_hash)
    )
    con.commit()
    con.close()


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Conversion ─────────────────────────────────────────────────────────────────

def convert_words(words: list[dict], mode: str) -> list[dict]:
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

init_db()

st.set_page_config(page_title="Video Caption Dashboard", layout="wide")
st.title("Video Caption Dashboard")

# Persistent temp dir
if "tmpdir" not in st.session_state or not os.path.exists(st.session_state["tmpdir"]):
    st.session_state["tmpdir"] = tempfile.mkdtemp()
    st.session_state.pop("video_path", None)
    st.session_state.pop("all_words", None)

tmpdir = st.session_state["tmpdir"]

uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"])

if uploaded:
    video_path = os.path.join(tmpdir, uploaded.name)
    with open(video_path, "wb") as f:
        f.write(uploaded.read())
    st.session_state["video_path"] = video_path
    st.session_state["filename"] = uploaded.name

if "video_path" in st.session_state:
    st.video(st.session_state["video_path"])

    caption_mode = st.radio("Caption language", ["Hinglish", "Hindi", "English"], horizontal=True)

    if st.button("Transcribe & Generate Captions"):
        file_hash = hash_file(st.session_state["video_path"])
        cached = get_cached(file_hash)

        if cached:
            st.success("Loaded from cache — no API calls made.")
            st.session_state["all_words"] = cached
            st.session_state["file_hash"] = file_hash
        else:
            with st.spinner("Extracting audio..."):
                wav_path = extract_audio(st.session_state["video_path"])
            with st.spinner("Transcribing..."):
                hindi_words = transcribe(wav_path)
            with st.spinner("Converting to Hinglish..."):
                hinglish_words = convert_words(hindi_words, "Hinglish")
            with st.spinner("Converting to English..."):
                english_words = convert_words(hindi_words, "English")

            all_words = {
                "Hindi": hindi_words,
                "Hinglish": hinglish_words,
                "English": english_words,
            }
            save_cache(file_hash, st.session_state["filename"], all_words)
            st.session_state["all_words"] = all_words
            st.session_state["file_hash"] = file_hash
            st.success("Transcription complete and saved to cache.")

    if "all_words" in st.session_state:
        words = st.session_state["all_words"][caption_mode]

        st.subheader("Transcription — edit if needed")
        edited = st.data_editor(
            words,
            column_config={
                "word": st.column_config.TextColumn("Word"),
                "start": st.column_config.NumberColumn("Start (s)", format="%.3f"),
                "end": st.column_config.NumberColumn("End (s)", format="%.3f"),
            },
            use_container_width=True,
            num_rows="dynamic",
        )

        if st.button("💾 Save Edits"):
            save_edits(st.session_state["file_hash"], caption_mode, edited)
            st.session_state["all_words"][caption_mode] = edited
            st.success(f"{caption_mode} edits saved.")

        if st.button("Burn Captions into Video"):
            output_path = os.path.join(tmpdir, "captioned.mp4")
            with st.spinner("Rendering video... this may take a minute"):
                add_captions(st.session_state["video_path"], edited, output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Captioned Video",
                    data=f,
                    file_name=f"{st.session_state['filename'].rsplit('.', 1)[0]}_captioned.mp4",
                    mime="video/mp4",
                )
