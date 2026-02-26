import hashlib
import json
import os
import sqlite3
import tempfile
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI
from caption_video import extract_audio, transcribe, add_captions, add_effects

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


def get_cached(file_hash: str):
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
        result = json.loads(response.choices[0].message.content)["words"]
        # If GPT returns fewer words than input, pad with originals
        if len(result) < len(batch):
            result += batch[len(result):]
        converted.extend(result[:len(batch)])

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

tab_pipeline, tab_effects = st.tabs(["Caption Pipeline", "Add Effects Only"])

# ── Tab 1: full pipeline ────────────────────────────────────────────────────────
with tab_pipeline:
    uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"], key="upload_pipeline")

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
                captioned_path = os.path.join(tmpdir, "captioned.mp4")
                bar = st.progress(0, text="Burning captions…")
                add_captions(st.session_state["video_path"], edited, captioned_path,
                             progress_callback=lambda v: bar.progress(v, text=f"Burning captions… {int(v*100)}%"))
                bar.progress(1.0, text="Done!")
                st.session_state["captioned_path"] = captioned_path

            if "captioned_path" in st.session_state and os.path.exists(st.session_state["captioned_path"]):
                with open(st.session_state["captioned_path"], "rb") as f:
                    st.download_button(
                        label="⬇️ Download Captioned Video",
                        data=f,
                        file_name=f"{st.session_state['filename'].rsplit('.', 1)[0]}_captioned.mp4",
                        mime="video/mp4",
                        key="dl_captioned_pipeline",
                    )

                st.subheader("Step 3 — Add Effects")
                st.caption("Face-tracking zoom + zoom punch every 2 s.")
                if st.button("✨ Add Effects", key="fx_pipeline"):
                    effects_path = os.path.join(tmpdir, "captioned_effects.mp4")
                    bar = st.progress(0, text="Scanning for faces…")
                    def _fx_cb_pipeline(v):
                        if v < 0.4:
                            bar.progress(v, text=f"Scanning for faces… {int(v / 0.4 * 100)}%")
                        else:
                            bar.progress(v, text=f"Rendering… {int((v - 0.4) / 0.6 * 100)}%")
                    add_effects(st.session_state["captioned_path"], effects_path, progress_callback=_fx_cb_pipeline)
                    bar.progress(1.0, text="Done!")
                    st.session_state["effects_path"] = effects_path

                if "effects_path" in st.session_state and os.path.exists(st.session_state["effects_path"]):
                    with open(st.session_state["effects_path"], "rb") as f:
                        st.download_button(
                            label="⬇️ Download Video with Effects",
                            data=f,
                            file_name=f"{st.session_state['filename'].rsplit('.', 1)[0]}_effects.mp4",
                            mime="video/mp4",
                            key="dl_effects_pipeline",
                        )

# ── Tab 2: effects only ─────────────────────────────────────────────────────────
with tab_effects:
    st.write("Upload an already-captioned video to apply Ken Burns zoom effects.")
    fx_uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"], key="upload_effects")

    if fx_uploaded:
        fx_input_path = os.path.join(tmpdir, "fx_input_" + fx_uploaded.name)
        with open(fx_input_path, "wb") as f:
            f.write(fx_uploaded.read())
        st.session_state["fx_input_path"] = fx_input_path
        st.session_state["fx_filename"] = fx_uploaded.name

    if "fx_input_path" in st.session_state and os.path.exists(st.session_state["fx_input_path"]):
        st.video(st.session_state["fx_input_path"])

        if st.button("✨ Add Effects", key="fx_standalone"):
            fx_output_path = os.path.join(tmpdir, "fx_output.mp4")
            bar = st.progress(0, text="Scanning for faces…")
            def _fx_cb_standalone(v):
                if v < 0.4:
                    bar.progress(v, text=f"Scanning for faces… {int(v / 0.4 * 100)}%")
                else:
                    bar.progress(v, text=f"Rendering… {int((v - 0.4) / 0.6 * 100)}%")
            add_effects(st.session_state["fx_input_path"], fx_output_path, progress_callback=_fx_cb_standalone)
            bar.progress(1.0, text="Done!")
            st.session_state["fx_output_path"] = fx_output_path

        if "fx_output_path" in st.session_state and os.path.exists(st.session_state["fx_output_path"]):
            with open(st.session_state["fx_output_path"], "rb") as f:
                st.download_button(
                    label="⬇️ Download Video with Effects",
                    data=f,
                    file_name=f"{st.session_state['fx_filename'].rsplit('.', 1)[0]}_effects.mp4",
                    mime="video/mp4",
                    key="dl_effects_standalone",
                )
