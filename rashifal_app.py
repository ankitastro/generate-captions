import os, sys, wave as wav_mod, time, json
import streamlit as st
from datetime import date, timedelta
from dotenv import load_dotenv

# ── Path setup so we can import from this directory ───────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_KEY       = "AIzaSyDn74Pp5vtA_MDP1Myo5kZzm7GQw-dtFSQ"
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION     = os.getenv("AZURE_REGION")
KUNDALI_URL      = "http://localhost:9090/api/v1/kundali"
ASSETS           = "/Users/ankitgupta/rashifal_creator/Rashifal_assets"
FONTS_DIR        = os.path.join(os.path.dirname(__file__), "fonts")
WAV1, WAV2       = "/tmp/rashi_p1.wav", "/tmp/rashi_p2.wav"

PART1_NAMES  = ["मेष", "वृषभ", "मिथुन", "कर्क", "Leo", "कन्या"]
PART2_NAMES  = ["तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
SIGNS_ORDER  = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
HOUSE_MEANING = {1:"स्वयं",2:"धन",3:"संचार",4:"घर",5:"प्रेम/सृजन",
                 6:"स्वास्थ्य/शत्रु",7:"जीवनसाथी",8:"रहस्य",9:"भाग्य/यात्रा",
                 10:"करियर",11:"लाभ/मित्र",12:"हानि/नींद"}

# ── Lazy imports (heavy libs load only when needed) ───────────────────────────
@st.cache_resource
def _load_libs():
    import google.genai as genai
    import google.genai.types as types
    import azure.cognitiveservices.speech as speechsdk
    import requests
    from build_rashifal_video import (
        get_timestamps, detect_boundaries, build_video,
        RASHI_VIDEO, BOUNDARY_MAP,
    )
    return genai, types, speechsdk, requests, get_timestamps, detect_boundaries, build_video, RASHI_VIDEO, BOUNDARY_MAP


# ── Gemini helpers ─────────────────────────────────────────────────────────────
def _gemini_client():
    genai, *_ = _load_libs()
    return genai.Client(api_key=GEMINI_KEY)


def fetch_transits(date_str):
    _, _, _, requests, *_ = _load_libs()
    resp = requests.get(f"{KUNDALI_URL}/horoscope/transits?date={date_str}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_sign_context(planets, aspects):
    sign_data = {}
    for sign in SIGNS_ORDER:
        si = SIGNS_ORDER.index(sign)
        houses = {}
        for planet, data in planets.items():
            pi = SIGNS_ORDER.index(data["rashi"])
            houses.setdefault(((pi - si) % 12) + 1, []).append(planet)
        sign_data[sign] = " | ".join(
            [f"भाव{h}({HOUSE_MEANING[h]}): {', '.join(v)}"
             for h, v in sorted(houses.items()) if v][:5]
        )
    moon_sign  = planets["Moon"]["rashi"]
    aspect_str = ", ".join([f"{a['planet1']} {a['aspect']} {a['planet2']}" for a in aspects])
    return sign_data, moon_sign, aspect_str


SYSTEM_PROMPT = """तुम एक नाटकीय और पंच भरा राशिफल लिखने वाले ज्योतिषी हो।
नियम:
- पूरा राशिफल शुद्ध देवनागरी हिंदी में लिखो
- सिर्फ hook English में (जैसे "Expense Alert:", "Danger Zone:", "Health Alert:", "Love Trap:", "Warning:", "Ego Clash:")
- 2-3 वाक्य, बोलचाल की भाषा, नाटकीय, असली जिंदगी की बातें
- Leo राशि का नाम "Leo" ही रखो, बाकी देवनागरी में
- कोई bold/asterisk नहीं, सिर्फ plain text
FORMAT: [राशि नाम]  [hook]: देवनागरी वाक्य"""


def generate_text(date_str, names, sign_list, sign_data, moon_sign, aspect_str):
    genai, types, *_ = _load_libs()
    client = _gemini_client()
    msg  = f"तारीख: {date_str}\nचंद्रमा: {moon_sign}. ग्रह: {aspect_str}\n\n"
    msg += "\n".join([f"{names[i]} ({sign_list[i]}): {sign_data[sign_list[i]]}"
                      for i in range(len(names))])
    msg += f"\n\nराशिफल लिखो: {', '.join(names)}"
    resp = client.models.generate_content(
        model="gemini-2.0-flash", contents=msg,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.85),
    )
    return resp.text


def generate_tts(text, out_path):
    genai, types, *_ = _load_libs()
    client = _gemini_client()
    r = client.models.generate_content(
        model="gemini-2.5-pro-preview-tts", contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Laomedeia"))),
        ),
    )
    data = r.candidates[0].content.parts[0].inline_data.data
    import wave
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000)
        wf.writeframes(data)
    return len(data) / 24000 / 2  # duration in seconds


def wav_duration(path):
    with wav_mod.open(path) as wf:
        return wf.getnframes() / wf.getframerate()


# ── Streamlit page config ──────────────────────────────────────────────────────
st.set_page_config(page_title="Rashifal Creator", page_icon="🔯", layout="wide")
st.title("🔯 Rashifal Creator")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    selected_date = st.date_input(
        "Rashifal Date",
        value=date.today() + timedelta(days=1),
        min_value=date(2020, 1, 1),
    )
    date_str = selected_date.strftime("%Y-%m-%d")
    st.caption(f"Date: `{date_str}`")
    st.divider()
    st.caption("Kundali Engine: `localhost:9090`")
    st.caption("TTS: Gemini 2.5 Pro · Laomedeia")
    st.caption("ASR: Azure hi-IN")

# ── Session state init ─────────────────────────────────────────────────────────
for key in ["text_p1", "text_p2", "dur1", "dur2", "words1", "words2", "date_used"]:
    if key not in st.session_state:
        st.session_state[key] = None

text_ready       = bool(st.session_state.text_p1 and st.session_state.text_p2)
audio_ready      = bool(st.session_state.dur1 and st.session_state.dur2)
timestamps_ready = bool(st.session_state.words1 and st.session_state.words2)

# ── STEP 1: Generate Text ──────────────────────────────────────────────────────
st.subheader("Step 1 — Generate Text")

col_btn1, col_info1 = st.columns([1, 4])
with col_btn1:
    gen_text_btn = st.button("Generate Text", type="primary", use_container_width=True)

if gen_text_btn:
    try:
        with st.spinner("Fetching planetary transits..."):
            t = fetch_transits(date_str)
        sign_data, moon_sign, aspect_str = build_sign_context(t["planets"], t["aspects"])

        with st.spinner("Generating Part 1 rashifal (मेष → कन्या)..."):
            p1 = generate_text(date_str, PART1_NAMES, SIGNS_ORDER[:6], sign_data, moon_sign, aspect_str)

        with st.spinner("Generating Part 2 rashifal (तुला → मीन)..."):
            p2 = generate_text(date_str, PART2_NAMES, SIGNS_ORDER[6:], sign_data, moon_sign, aspect_str)

        st.session_state.text_p1    = p1
        st.session_state.text_p2    = p2
        st.session_state.date_used  = date_str
        # Reset downstream state when text is regenerated
        st.session_state.dur1   = None
        st.session_state.dur2   = None
        st.session_state.words1 = None
        st.session_state.words2 = None
        st.rerun()
    except Exception as e:
        st.error(f"Text generation failed: {e}")

if text_ready:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Part 1 — मेष → कन्या")
        edited_p1 = st.text_area("", value=st.session_state.text_p1,
                                  height=280, key="edit_p1", label_visibility="collapsed")
        if edited_p1 != st.session_state.text_p1:
            st.session_state.text_p1 = edited_p1
    with c2:
        st.caption("Part 2 — तुला → मीन")
        edited_p2 = st.text_area("", value=st.session_state.text_p2,
                                  height=280, key="edit_p2", label_visibility="collapsed")
        if edited_p2 != st.session_state.text_p2:
            st.session_state.text_p2 = edited_p2
    if st.session_state.date_used and st.session_state.date_used != date_str:
        st.warning(f"Text was generated for **{st.session_state.date_used}**, not {date_str}. Re-generate to update.")

st.divider()

# ── STEP 2: Generate Audio ─────────────────────────────────────────────────────
st.subheader("Step 2 — Generate Audio")

col_btn2, _ = st.columns([1, 4])
with col_btn2:
    gen_audio_btn = st.button(
        "Generate Audio", type="primary",
        disabled=not text_ready,
        use_container_width=True,
    )

if not text_ready:
    st.caption("Complete Step 1 first.")

if gen_audio_btn and text_ready:
    try:
        with st.spinner("Generating TTS for Part 1 (~30s)..."):
            dur1 = generate_tts(st.session_state.text_p1, WAV1)
        with st.spinner("Generating TTS for Part 2 (~30s)..."):
            dur2 = generate_tts(st.session_state.text_p2, WAV2)

        st.session_state.dur1   = dur1
        st.session_state.dur2   = dur2
        # Reset downstream state when audio is regenerated
        st.session_state.words1 = None
        st.session_state.words2 = None
        st.rerun()
    except Exception as e:
        st.error(f"Audio generation failed: {e}")

if audio_ready:
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"Part 1 — {st.session_state.dur1:.1f}s")
        if os.path.exists(WAV1):
            st.audio(WAV1)
    with c2:
        st.caption(f"Part 2 — {st.session_state.dur2:.1f}s")
        if os.path.exists(WAV2):
            st.audio(WAV2)

st.divider()

# ── STEP 3: Generate Timestamps ───────────────────────────────────────────────
st.subheader("Step 3 — Generate Timestamps")

col_btn3, _ = st.columns([1, 4])
with col_btn3:
    gen_ts_btn = st.button(
        "Generate Timestamps", type="primary",
        disabled=not audio_ready,
        use_container_width=True,
    )

if not audio_ready:
    st.caption("Complete Step 2 first.")

if gen_ts_btn and audio_ready:
    try:
        _, _, _, _, get_timestamps_fn, *_ = _load_libs()

        with st.spinner("Getting word timestamps for Part 1 (Azure hi-IN)..."):
            words1 = get_timestamps_fn(WAV1)
        with st.spinner("Getting word timestamps for Part 2 (Azure hi-IN)..."):
            words2 = get_timestamps_fn(WAV2)

        st.session_state.words1 = words1
        st.session_state.words2 = words2
        st.rerun()
    except Exception as e:
        st.error(f"Timestamp generation failed: {e}")

if timestamps_ready:
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"Part 1 — {len(st.session_state.words1)} words recognized")
        st.caption(" · ".join(w["word"] for w in st.session_state.words1[:8]) + " …")
    with c2:
        st.caption(f"Part 2 — {len(st.session_state.words2)} words recognized")
        st.caption(" · ".join(w["word"] for w in st.session_state.words2[:8]) + " …")

st.divider()

# ── STEP 4: Build Videos ───────────────────────────────────────────────────────
st.subheader("Step 4 — Build Videos")

OUT1 = f"/tmp/rashifal_{date_str}_part1.mp4"
OUT2 = f"/tmp/rashifal_{date_str}_part2.mp4"

col_btn4, _ = st.columns([1, 4])
with col_btn4:
    build_btn = st.button(
        "Build Videos", type="primary",
        disabled=not timestamps_ready,
        use_container_width=True,
    )

if not timestamps_ready:
    st.caption("Complete Step 3 first.")

if build_btn and timestamps_ready:
    _, _, _, _, _, _, build_video_fn, *_ = _load_libs()
    try:
        with st.spinner("Building Part 1 video (may take 1-2 min)..."):
            build_video_fn(PART1_NAMES, st.session_state.words1, WAV1,
                           st.session_state.dur1, OUT1)
        with st.spinner("Building Part 2 video (may take 1-2 min)..."):
            build_video_fn(PART2_NAMES, st.session_state.words2, WAV2,
                           st.session_state.dur2, OUT2)
        st.success("Videos built!")
        st.rerun()
    except Exception as e:
        st.error(f"Video build failed: {e}")

if os.path.exists(OUT1) and os.path.exists(OUT2):
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Part 1 — मेष → कन्या")
        st.video(OUT1)
        with open(OUT1, "rb") as f:
            st.download_button("Download Part 1", f.read(),
                               file_name=f"rashifal_{date_str}_part1.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        st.caption("Part 2 — तुला → मीन")
        st.video(OUT2)
        with open(OUT2, "rb") as f:
            st.download_button("Download Part 2", f.read(),
                               file_name=f"rashifal_{date_str}_part2.mp4",
                               mime="video/mp4", use_container_width=True)
