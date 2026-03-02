# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the apps

```bash
# Activate venv first (always)
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate             # Windows

# Rashifal video creator (primary app)
streamlit run rashifal_app.py --server.port 8502

# Generic video captioning app
streamlit run app.py --server.port 8501

# Kundali engine (must be running for rashifal_app.py to work)
cd kundali-engine
uvicorn main:app --host 0.0.0.0 --port 9090
```

## Architecture

Two independent Streamlit apps share a common processing layer:

**`rashifal_app.py`** — 7-step pipeline UI for daily horoscope videos:
1. Fetch planetary transits from kundali-engine → generate Hindi rashifal text (Gemini 2.5 Flash)
2. Edit text in UI (edits stored in `st.session_state.edit_p1/edit_p2`, NOT `text_p1/text_p2`)
3. TTS via Gemini `gemini-2.5-pro-preview-tts` (Laomedeia voice) → WAV files in `tempfile.gettempdir()`
4. Word-level timestamps via Azure hi-IN ASR
5. Build video: loop rashi MP4 assets, detect zodiac sign boundaries, burn captions at `H*0.50`
6. Prepend intro + append outro via ffmpeg `filter_complex` concat (re-encode to 720×1280)
7. Mix background music + overlay logo (bottom-right) + date text (below captions) via ffmpeg

**`app.py`** — Generic video captioning: upload → transcribe → Hinglish conversion → burn captions with optional Ken Burns zoom.

**`build_rashifal_video.py`** — Imported by `rashifal_app.py`. Contains boundary detection, caption drawing, and `build_video()`. All temp paths use `tempfile.gettempdir()` for cross-platform compatibility.

**`kundali-engine/`** — FastAPI microservice (port 9090). `rashifal_app.py` calls `/api/v1/kundali/horoscope/transits?date=<DATE>` to get planetary positions used for text generation.

## Key implementation details

**Zodiac boundary detection** (`build_rashifal_video.py`):
- `_BOUNDARY_LOWER` is a case-insensitive lookup dict built at import time from `BOUNDARY_MAP`
- Always use `_BOUNDARY_LOWER.get(raw.lower())` — never add capitalised duplicates to `BOUNDARY_MAP`
- Short names (≤4 chars: mesh, kark, tula, meen) are in `BOUNDARY_MAP` only — NOT in `FUZZY_RASHI` — to prevent false positives (e.g. "karke" → कर्क)
- `build_video()` returns `False` and aborts if any sign is missing; caller must handle this
- Leo has many aliases: leo, lio, singh, sighn, sign, लियो, लिओ, सिंह

**Session state pattern** (Streamlit):
- Text area edits use `key="edit_p1"` / `key="edit_p2"` — never pass `value=` to a text_area that has a `key`, as it overrides user edits on every rerun
- TTS always reads from `st.session_state.edit_p1` / `edit_p2`, not `text_p1` / `text_p2`

**Background thread logging** (Step 4 build):
- `build_video()` runs in a background thread; logs go to a file via `log_fn` callback
- Main thread polls the file every 1s and updates `st.empty().code()` — never use `st.session_state` from a background thread

**ffmpeg usage** (Steps 5–7):
- Always use `filter_complex` concat with `scale=720:1280,setsar=1,fps=30` and `aresample=44100` when joining clips — avoids resolution mismatch errors
- Step 7 re-encodes with `libx264` (not `-c:v copy`) because video filters (logo overlay, drawtext) are applied

## Asset paths

```
assets/
  part1/The_lady_in_202601151151_hdnib.mp4   # Intro Part 1
  part2/The_lady_in_202601151147_u7x9c.mp4   # Intro Part 2
  dressUp_cta_captioned.mp4                   # Outro (shared)
  bg_music.mp3                                # Background music
  astrokiran_logo.png                         # Watermark logo
fonts/
  Arial-Bold.ttf
  ITFDevanagari.ttc
```

All asset paths are repo-relative via `os.path.join(os.path.dirname(__file__), ...)`.

## Environment variables (`.env`)

```
GEMINI_API_KEY=
AZURE_SPEECH_KEY=
AZURE_REGION=
```

## Database

`rashifal.db` (SQLite) — sessions table keyed by date, stores `text_p1`, `text_p2`, `dur1`, `dur2`, and word timestamps. Auto-loaded when the date picker changes.
