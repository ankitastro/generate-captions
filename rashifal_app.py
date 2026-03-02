import os, sys, wave as wav_mod, time, json, sqlite3, tempfile
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_KEY       = os.getenv("GEMINI_API_KEY")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION     = os.getenv("AZURE_REGION")
KUNDALI_URL      = "http://localhost:9090/api/v1/kundali"
FONTS_DIR        = os.path.join(os.path.dirname(__file__), "fonts")
_TMP             = tempfile.gettempdir()
WAV1, WAV2       = os.path.join(_TMP, "rashi_p1.wav"), os.path.join(_TMP, "rashi_p2.wav")
BUILD_LOG        = os.path.join(_TMP, "rashifal_build.log")
DB_PATH          = os.path.join(os.path.dirname(__file__), "rashifal.db")

PART1_NAMES  = ["मेष", "वृषभ", "मिथुन", "कर्क", "Leo", "कन्या"]
PART2_NAMES  = ["तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
SIGNS_ORDER  = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
HOUSE_MEANING = {1:"स्वयं",2:"धन",3:"संचार",4:"घर",5:"प्रेम/सृजन",
                 6:"स्वास्थ्य/शत्रु",7:"जीवनसाथी",8:"रहस्य",9:"भाग्य/यात्रा",
                 10:"करियर",11:"लाभ/मित्र",12:"हानि/नींद"}

NAKSHATRAS = [
    "अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा",
    "पुनर्वसु","पुष्य","आश्लेषा","मघा","पूर्व फाल्गुनी","उत्तर फाल्गुनी",
    "हस्त","चित्रा","स्वाति","विशाखा","अनुराधा","ज्येष्ठा",
    "मूल","पूर्व आषाढ़","उत्तर आषाढ़","श्रवण","धनिष्ठा","शतभिषा",
    "पूर्व भाद्रपद","उत्तर भाद्रपद","रेवती",
]
WEEKDAYS_HI = ["सोमवार","मंगलवार","बुधवार","गुरुवार","शुक्रवार","शनिवार","रविवार"]

def moon_nakshatra(longitude):
    return NAKSHATRAS[int(longitude / (360 / 27))]

def day_of_week_hi(date_str):
    from datetime import datetime
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return WEEKDAYS_HI[d.weekday()]

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_db() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                date        TEXT PRIMARY KEY,
                text_p1     TEXT,
                text_p2     TEXT,
                dur1        REAL,
                dur2        REAL,
                updated_at  TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS timestamps (
                date        TEXT,
                part        INTEGER,
                words       TEXT,
                updated_at  TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (date, part)
            );
        """)

init_db()

def db_save_session(date_str, **kwargs):
    """Upsert session fields (text_p1, text_p2, dur1, dur2) for a date."""
    with get_db() as con:
        # Insert row if missing, then update only the supplied fields
        con.execute("INSERT OR IGNORE INTO sessions (date) VALUES (?)", (date_str,))
        for col, val in kwargs.items():
            con.execute(f"UPDATE sessions SET {col}=?, updated_at=datetime('now') WHERE date=?",
                        (val, date_str))

def db_load_session(date_str):
    with get_db() as con:
        row = con.execute(
            "SELECT text_p1, text_p2, dur1, dur2 FROM sessions WHERE date=?", (date_str,)
        ).fetchone()
    if row:
        return {"text_p1": row[0], "text_p2": row[1], "dur1": row[2], "dur2": row[3]}
    return None

def db_save_timestamps(date_str, part, words):
    with get_db() as con:
        con.execute("""
            INSERT INTO timestamps (date, part, words, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(date, part) DO UPDATE SET words=excluded.words, updated_at=excluded.updated_at
        """, (date_str, part, json.dumps(words, ensure_ascii=False)))

def db_load_timestamps(date_str, part):
    with get_db() as con:
        row = con.execute(
            "SELECT words FROM timestamps WHERE date=? AND part=?", (date_str, part)
        ).fetchone()
    return json.loads(row[0]) if row else None

def db_list_dates():
    with get_db() as con:
        rows = con.execute(
            "SELECT date, dur1, dur2 FROM sessions WHERE text_p1 IS NOT NULL ORDER BY date DESC LIMIT 30"
        ).fetchall()
    return rows

# ── Lazy imports ──────────────────────────────────────────────────────────────
def _load_libs():
    import google.genai as genai
    import google.genai.types as types
    import azure.cognitiveservices.speech as speechsdk
    import requests
    from build_rashifal_video import (
        get_timestamps, detect_boundaries, build_video,
        RASHI_VIDEO, BOUNDARY_MAP,
    )
    from caption_video import to_hinglish
    return genai, types, speechsdk, requests, get_timestamps, detect_boundaries, build_video, RASHI_VIDEO, BOUNDARY_MAP, to_hinglish

# ── API helpers ───────────────────────────────────────────────────────────────
def _gemini_client():
    genai, *_ = _load_libs()
    return genai.Client(api_key=GEMINI_KEY)

def fetch_transits(date_str):
    _, _, _, requests, *_ = _load_libs()
    resp = requests.get(f"{KUNDALI_URL}/horoscope/transits?date={date_str}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_sign_context(planets, aspects, date_str):
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
    moon_sign   = planets["Moon"]["rashi"]
    nakshatra   = moon_nakshatra(planets["Moon"]["longitude"])
    weekday     = day_of_week_hi(date_str)
    # top 3 aspects only
    aspect_str  = ", ".join([f"{a['planet1']} {a['aspect']} {a['planet2']}" for a in aspects[:3]])
    # planet positions summary (Sun, Moon, Mars, Jupiter, Saturn)
    key_planets = ["Sun","Moon","Mars","Jupiter","Saturn"]
    planet_str  = ", ".join(
        [f"{p} {planets[p]['rashi']} {planets[p]['degrees']:.1f}°"
         for p in key_planets if p in planets]
    )
    return sign_data, moon_sign, nakshatra, weekday, aspect_str, planet_str

SYSTEM_PROMPT = """तुम एक नाटकीय और पंच भरा राशिफल लिखने वाले ज्योतिषी हो।
नियम:
- पूरा राशिफल शुद्ध देवनागरी हिंदी में लिखो
- सिर्फ hook English में (जैसे "Expense Alert:", "Danger Zone:", "Health Alert:", "Love Trap:", "Warning:", "Ego Clash:")
- सिर्फ 2 वाक्य — ज़्यादा नहीं। हर वाक्य छोटा और तीखा हो।
- बोलचाल की भाषा, नाटकीय, असली जिंदगी की बातें
- दिए गए नक्षत्र, वार, और ग्रह स्थिति के आधार पर लिखो — हर दिन का राशिफल अलग होना चाहिए
- Leo राशि का नाम "Leo" ही रखो, बाकी देवनागरी में
- कोई bold/asterisk नहीं, सिर्फ plain text
- हर राशि की शुरुआत अलग-अलग तरीके से करो — "आज आप", "आज", "इस वक्त" जैसे एक ही शब्द बार-बार मत दोहराओ
- विविध शुरुआत: कभी सीधे situation से शुरू करो, कभी warning से, कभी सवाल से, कभी emotion से

उदाहरण (हर राशि की अलग शुरुआत देखो):
मेष  Expense Alert: अचानक जेब पर बोझ पड़ सकता है। किसी दोस्त या रिश्तेदार के लिए खर्च करने से पहले दो बार सोचो।
वृषभ  घर में सुकून चाहिए था, पर मेहमान या अचानक का काम सब चौपट कर सकता है। धैर्य रखना ही समझदारी है।
मिथुन  Danger Zone: एक छोटी सी बात को बड़ा मत बनाओ। पार्टनर या दोस्त के साथ गलतफहमी में प्लान डूब सकता है।
कर्क  Money Alert: पैसा हाथ से निकलने वाला है — रोको या पछताओ। किसी को उधार देना आज भारी पड़ेगा।
Leo  Ego Clash: मूड ज़रूरत से ज़्यादा dramatic है, संभालो। हर कोई तुम्हारी बात माने ये ज़रूरी नहीं।
कन्या  Health Alert: काम का बोझ शरीर पर भारी पड़ रहा है — थोड़ा रुको। कोई छुपी बात मन में उथल-पुथल मचा सकती है।

FORMAT: [राशि नाम]  [hook (optional)]: देवनागरी में सिर्फ 2 वाक्य"""

def generate_text(date_str, names, sign_list, sign_data, moon_sign, nakshatra, weekday, aspect_str, planet_str):
    genai, types, *_ = _load_libs()
    client = _gemini_client()
    msg  = f"📅 तारीख: {date_str} ({weekday})\n"
    msg += f"🌙 चंद्रमा: {moon_sign} राशि, {nakshatra} नक्षत्र\n"
    msg += f"🪐 ग्रह स्थिति: {planet_str}\n"
    msg += f"⚡ मुख्य योग: {aspect_str}\n\n"
    msg += "हर राशि के लिए भाव स्थिति:\n"
    msg += "\n".join([f"{names[i]} ({sign_list[i]}): {sign_data[sign_list[i]]}"
                      for i in range(len(names))])
    msg += f"\n\nऊपर दी गई {date_str} ({weekday}) की ग्रह स्थिति और {nakshatra} नक्षत्र के आधार पर इन राशियों का राशिफल लिखो: {', '.join(names)}"
    resp = client.models.generate_content(
        model="gemini-2.5-flash", contents=msg,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.9,
            thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking for speed
        ),
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
    return len(data) / 24000 / 2

def wav_duration(path):
    with wav_mod.open(path) as wf:
        return wf.getnframes() / wf.getframerate()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Rashifal Creator", page_icon="🔯", layout="wide")
st.title("🔯 Rashifal Creator")

# ── Sidebar ───────────────────────────────────────────────────────────────────
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def _save_upload(uploaded, dest_path):
    """Save an st.uploaded_file to dest_path, return True on success."""
    if uploaded is None:
        return False
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(uploaded.read())
    return True

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
    st.divider()

    st.divider()
    st.subheader("Previous Sessions")
    past = db_list_dates()
    if past:
        for row in past:
            audio_info = f" · {row[1]:.0f}s+{row[2]:.0f}s" if row[1] else ""
            st.caption(f"📅 {row[0]}{audio_info}")
    else:
        st.caption("No saved sessions yet.")

# ── Assets Management ─────────────────────────────────────────────────────────
_RASHI_FILES = {
    "Aries (मेष)":       ("rashi/part1", "aries.mp4"),
    "Taurus (वृषभ)":     ("rashi/part1", "taurus.mp4"),
    "Gemini (मिथुन)":    ("rashi/part1", "mithun.mp4"),
    "Cancer (कर्क)":     ("rashi/part1", "cancer.mp4"),
    "Leo":               ("rashi/part1", "leo.mp4"),
    "Virgo (कन्या)":     ("rashi/part1", "virgo.mp4"),
    "Libra (तुला)":      ("rashi/part2", "libra.mp4"),
    "Scorpio (वृश्चिक)": ("rashi/part2", "scorpion.mp4"),
    "Sagittarius (धनु)": ("rashi/part2", "sagitarius.mp4"),
    "Capricorn (मकर)":   ("rashi/part2", "capriocpon.mp4"),
    "Aquarius (कुंभ)":   ("rashi/part2", "aquarius.mp4"),
    "Pisces (मीन)":      ("rashi/part2", "pieces.mp4"),
}

with st.expander("Assets", expanded=False):
    st.caption("Preview current assets or upload to replace them permanently.")

    # ── Main assets ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("**Intro Video**")
        p = os.path.join(_ASSETS_DIR, "intro.mp4")
        if os.path.exists(p): st.video(p)
        up = st.file_uploader("Replace Intro", type=["mp4"], key="up_intro")
        if _save_upload(up, p): st.success("Updated")
    with c2:
        st.caption("**Outro Video**")
        p = os.path.join(_ASSETS_DIR, "dressUp_cta_captioned.mp4")
        if os.path.exists(p): st.video(p)
        up = st.file_uploader("Replace Outro", type=["mp4"], key="up_outro")
        if _save_upload(up, p): st.success("Updated")
    with c3:
        st.caption("**Logo**")
        p = os.path.join(_ASSETS_DIR, "astrokiran_logo.png")
        if os.path.exists(p): st.image(p)
        up = st.file_uploader("Replace Logo", type=["png"], key="up_logo")
        if _save_upload(up, p): st.success("Updated")

    st.caption("**Background Music**")
    p = os.path.join(_ASSETS_DIR, "bg_music.mp3")
    if os.path.exists(p): st.audio(p)
    up = st.file_uploader("Replace Background Music", type=["mp3", "m4a", "wav"], key="up_bgm")
    if _save_upload(up, p): st.success("Updated")

    # ── Rashi sign videos ────────────────────────────────────────────────────
    st.caption("**Rashi Sign Videos**")
    cols = st.columns(4)
    for i, (label, (subdir, fname)) in enumerate(_RASHI_FILES.items()):
        p = os.path.join(_ASSETS_DIR, subdir, fname)
        with cols[i % 4]:
            st.caption(f"**{label}**")
            if os.path.exists(p): st.video(p)
            up = st.file_uploader("Replace", type=["mp4"], key=f"up_rashi_{fname}")
            if _save_upload(up, p): st.success("Updated")

st.divider()

# ── Session state init ────────────────────────────────────────────────────────
for key in ["text_p1", "text_p2", "edit_p1", "edit_p2", "dur1", "dur2", "words1", "words2", "loaded_date"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Auto-load from DB when date changes
if st.session_state.loaded_date != date_str:
    session = db_load_session(date_str)
    if session:
        st.session_state.text_p1 = session["text_p1"]
        st.session_state.text_p2 = session["text_p2"]
        st.session_state.edit_p1 = session["text_p1"]
        st.session_state.edit_p2 = session["text_p2"]
        st.session_state.dur1    = session["dur1"]
        st.session_state.dur2    = session["dur2"]
    else:
        st.session_state.text_p1 = None
        st.session_state.text_p2 = None
        st.session_state.edit_p1 = None
        st.session_state.edit_p2 = None
        st.session_state.dur1    = None
        st.session_state.dur2    = None
    st.session_state.words1 = db_load_timestamps(date_str, 1)
    st.session_state.words2 = db_load_timestamps(date_str, 2)
    st.session_state.loaded_date = date_str

text_ready       = bool(st.session_state.edit_p1 and st.session_state.edit_p2)
audio_ready      = bool(st.session_state.dur1 and st.session_state.dur2)
timestamps_ready = bool(st.session_state.words1 and st.session_state.words2)

# ── STEP 1: Generate Text ─────────────────────────────────────────────────────
st.subheader("Step 1 — Generate Text")

col_btn1, _ = st.columns([1, 4])
with col_btn1:
    gen_text_btn = st.button("Generate Text", type="primary", use_container_width=True)

if gen_text_btn:
    try:
        with st.spinner("Fetching planetary transits..."):
            t = fetch_transits(date_str)
        sign_data, moon_sign, nakshatra, weekday, aspect_str, planet_str = build_sign_context(t["planets"], t["aspects"], date_str)
        with st.spinner("Generating rashifal for all 12 rashis in parallel..."):
            from concurrent.futures import ThreadPoolExecutor
            args = (date_str, sign_data, moon_sign, nakshatra, weekday, aspect_str, planet_str)
            with ThreadPoolExecutor(max_workers=2) as ex:
                f1 = ex.submit(generate_text, *args[:1], PART1_NAMES, SIGNS_ORDER[:6], *args[1:])
                f2 = ex.submit(generate_text, *args[:1], PART2_NAMES, SIGNS_ORDER[6:], *args[1:])
                p1, p2 = f1.result(), f2.result()
        st.session_state.text_p1 = p1
        st.session_state.text_p2 = p2
        st.session_state.edit_p1 = p1
        st.session_state.edit_p2 = p2
        st.session_state.dur1    = None
        st.session_state.dur2    = None
        st.session_state.words1  = None
        st.session_state.words2  = None
        db_save_session(date_str, text_p1=p1, text_p2=p2)
        st.rerun()
    except Exception as e:
        st.error(f"Text generation failed: {e}")

if text_ready:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Part 1 — मेष → कन्या")
        st.text_area("", height=280, key="edit_p1", label_visibility="collapsed",
                     on_change=lambda: db_save_session(date_str, text_p1=st.session_state.edit_p1))
    with c2:
        st.caption("Part 2 — तुला → मीन")
        st.text_area("", height=280, key="edit_p2", label_visibility="collapsed",
                     on_change=lambda: db_save_session(date_str, text_p2=st.session_state.edit_p2))

st.divider()

# ── STEP 2: Generate Audio ────────────────────────────────────────────────────
st.subheader("Step 2 — Generate Audio")

col_btn2, _ = st.columns([1, 4])
with col_btn2:
    gen_audio_btn = st.button("Generate Audio", type="primary",
                               disabled=not text_ready, use_container_width=True)

if not text_ready:
    st.caption("Complete Step 1 first.")

if gen_audio_btn and text_ready:
    try:
        with st.spinner("Generating TTS for Part 1 (~30s)..."):
            dur1 = generate_tts(st.session_state.edit_p1, WAV1)
        with st.spinner("Generating TTS for Part 2 (~30s)..."):
            dur2 = generate_tts(st.session_state.edit_p2, WAV2)
        st.session_state.dur1   = dur1
        st.session_state.dur2   = dur2
        st.session_state.words1 = None
        st.session_state.words2 = None
        db_save_session(date_str, dur1=dur1, dur2=dur2)
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
    gen_ts_btn = st.button("Generate Timestamps", type="primary",
                            disabled=not audio_ready, use_container_width=True)

if not audio_ready:
    st.caption("Complete Step 2 first.")

if gen_ts_btn and audio_ready:
    try:
        *_, get_timestamps_fn, _, _, _, _, to_hinglish_fn = _load_libs()
        with st.spinner("Getting word timestamps for Part 1 (Azure hi-IN)..."):
            raw1 = get_timestamps_fn(WAV1)
        with st.spinner("Converting Part 1 to Hinglish..."):
            words1 = to_hinglish_fn(raw1)
        with st.spinner("Getting word timestamps for Part 2 (Azure hi-IN)..."):
            raw2 = get_timestamps_fn(WAV2)
        with st.spinner("Converting Part 2 to Hinglish..."):
            words2 = to_hinglish_fn(raw2)
        st.session_state.words1 = words1
        st.session_state.words2 = words2
        db_save_timestamps(date_str, 1, words1)
        db_save_timestamps(date_str, 2, words2)
        st.rerun()
    except Exception as e:
        st.error(f"Timestamp generation failed: {e}")

if timestamps_ready:
    tab1, tab2 = st.tabs(["Part 1 — मेष → कन्या", "Part 2 — तुला → मीन"])

    def render_ts_editor(tab, words_key, part):
        with tab:
            df = pd.DataFrame(st.session_state[words_key])[["word", "start", "end"]]
            edited = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "word":  st.column_config.TextColumn("Word", width="medium"),
                    "start": st.column_config.NumberColumn("Start (s)", format="%.3f", step=0.001),
                    "end":   st.column_config.NumberColumn("End (s)",   format="%.3f", step=0.001),
                },
                key=f"ts_editor_{part}",
            )
            if st.button(f"Save Part {part} Timestamps", key=f"save_ts_{part}"):
                updated = edited.to_dict("records")
                st.session_state[words_key] = updated
                db_save_timestamps(date_str, part, updated)
                st.success(f"Part {part} timestamps saved to database.")

    render_ts_editor(tab1, "words1", 1)
    render_ts_editor(tab2, "words2", 2)

st.divider()

# ── STEP 4: Build Videos ──────────────────────────────────────────────────────
st.subheader("Step 4 — Build Videos")

OUT1 = os.path.join(_TMP, f"rashifal_{date_str}_part1.mp4")
OUT2 = os.path.join(_TMP, f"rashifal_{date_str}_part2.mp4")

videos_exist = os.path.exists(OUT1) and os.path.exists(OUT2)
wavs_exist   = os.path.exists(WAV1) and os.path.exists(WAV2)

col_build, col_rebuild, _ = st.columns([1, 1, 3])
with col_build:
    build_btn = st.button("Build Videos", type="primary",
                          disabled=not timestamps_ready,
                          use_container_width=True)
with col_rebuild:
    rebuild_btn = st.button("Rebuild", type="secondary",
                            disabled=not timestamps_ready or not videos_exist,
                            use_container_width=True)

if not timestamps_ready:
    st.caption("Complete Step 3 first.")
elif not wavs_exist:
    st.warning("Audio files missing from /tmp — please re-run Step 2 to regenerate.")

if (build_btn or rebuild_btn) and timestamps_ready:
    if not wavs_exist:
        st.error("Cannot build: WAV files missing. Re-run Step 2 first.")
    else:
        import threading, traceback as _tb
        _, _, _, _, _, _, build_video_fn, *_rest = _load_libs()

        for f in [OUT1, OUT2]:
            if os.path.exists(f):
                os.remove(f)

        # Capture session state in main thread
        words1 = list(st.session_state.words1)
        words2 = list(st.session_state.words2)
        dur1   = float(st.session_state.dur1)
        dur2   = float(st.session_state.dur2)

        # Clear log file and write header
        with open(BUILD_LOG, "w") as _f:
            _f.write(f"Build started: {date_str}\n")

        def _log(msg):
            with open(BUILD_LOG, "a") as _f:
                _f.write(str(msg) + "\n")

        build_err  = [None]
        build_done = [False]

        def _run():
            try:
                _log("=== Part 1 (मेष → कन्या) ===")
                ok1 = build_video_fn(PART1_NAMES, words1, WAV1, dur1, OUT1, log_fn=_log)
                if ok1 is False:
                    build_err[0] = ValueError("Part 1: not all zodiac signs detected — see log")
                    return
                _log("=== Part 2 (तुला → मीन) ===")
                ok2 = build_video_fn(PART2_NAMES, words2, WAV2, dur2, OUT2, log_fn=_log)
                if ok2 is False:
                    build_err[0] = ValueError("Part 2: not all zodiac signs detected — see log")
                    return
                _log("Done!")
            except Exception as e:
                _log(f"ERROR: {e}")
                _log("".join(_tb.format_exception(type(e), e, e.__traceback__)))
                build_err[0] = e
            finally:
                build_done[0] = True

        threading.Thread(target=_run, daemon=True).start()

        log_box = st.empty()
        while not build_done[0]:
            try:
                log_box.code(open(BUILD_LOG).read(), language=None)
            except Exception:
                pass
            time.sleep(1)

        # Final read after done
        try:
            log_box.code(open(BUILD_LOG).read(), language=None)
        except Exception:
            pass

        if build_err[0]:
            st.error(f"Video build failed: {build_err[0]}")
        else:
            st.success("Videos built!")
            st.rerun()

if os.path.exists(OUT1) and os.path.exists(OUT2):
    c1, c2 = st.columns(2)
    with c1:
        with open(OUT1, "rb") as f:
            st.download_button("Download Part 1", f.read(),
                               file_name=f"rashifal_{date_str}_part1.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        with open(OUT2, "rb") as f:
            st.download_button("Download Part 2", f.read(),
                               file_name=f"rashifal_{date_str}_part2.mp4",
                               mime="video/mp4", use_container_width=True)

st.divider()

# ── STEP 5: Prepend Intro ──────────────────────────────────────────────────────
st.subheader("Step 5 — Prepend Intro")

from build_rashifal_video import INTRO_VIDEO, OUTRO_VIDEO

FINAL1 = os.path.join(_TMP, f"rashifal_{date_str}_part1_final.mp4")
FINAL2 = os.path.join(_TMP, f"rashifal_{date_str}_part2_final.mp4")

finals_exist  = os.path.exists(FINAL1) and os.path.exists(FINAL2)
rashi_built   = os.path.exists(OUT1) and os.path.exists(OUT2)

col_intro, _ = st.columns([1, 4])
with col_intro:
    prepend_btn = st.button("Prepend Intro", type="primary",
                            disabled=not rashi_built,
                            use_container_width=True)

if not rashi_built:
    st.caption("Complete Step 4 first.")

if prepend_btn and rashi_built:
    import subprocess, traceback as _tb2
    try:
        for part, rashi_path, intro_path, final_path in [
            (1, OUT1, INTRO_VIDEO, FINAL1),
            (2, OUT2, INTRO_VIDEO, FINAL2),
        ]:
            if not os.path.exists(intro_path):
                st.error(f"Intro not found: {intro_path}")
                break
            with st.spinner(f"Prepending intro to Part {part}..."):
                result = subprocess.run(
                    ["ffmpeg", "-y",
                     "-i", intro_path, "-i", rashi_path,
                     "-filter_complex",
                     "[0:v]scale=720:1280,setsar=1,fps=30[v0];"
                     "[0:a]aresample=44100[a0];"
                     "[1:v]scale=720:1280,setsar=1,fps=30[v1];"
                     "[1:a]aresample=44100[a1];"
                     "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
                     "-map", "[v]", "-map", "[a]",
                     "-c:v", "libx264", "-c:a", "aac", final_path],
                    capture_output=True, text=True
                )
            if result.returncode != 0:
                st.error(f"Part {part} ffmpeg failed:")
                st.code(result.stderr, language=None)
                break
            st.success(f"Part {part} done → {final_path}")
        else:
            st.rerun()
    except Exception as e:
        st.error(f"Prepend failed: {e}")
        st.code("".join(_tb2.format_exception(type(e), e, e.__traceback__)), language=None)

if finals_exist:
    c1, c2 = st.columns(2)
    with c1:
        with open(FINAL1, "rb") as f:
            st.download_button("Download Part 1 (with intro)", f.read(),
                               file_name=f"rashifal_{date_str}_part1_final.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        with open(FINAL2, "rb") as f:
            st.download_button("Download Part 2 (with intro)", f.read(),
                               file_name=f"rashifal_{date_str}_part2_final.mp4",
                               mime="video/mp4", use_container_width=True)

st.divider()

# ── STEP 6: Append Outro ──────────────────────────────────────────────────────
st.subheader("Step 6 — Append Outro")

COMPLETE1 = os.path.join(_TMP, f"rashifal_{date_str}_part1_complete.mp4")
COMPLETE2 = os.path.join(_TMP, f"rashifal_{date_str}_part2_complete.mp4")

complete_exist = os.path.exists(COMPLETE1) and os.path.exists(COMPLETE2)

col_outro, _ = st.columns([1, 4])
with col_outro:
    outro_btn = st.button("Append Outro", type="primary",
                          disabled=not finals_exist,
                          use_container_width=True)

if not finals_exist:
    st.caption("Complete Step 5 first.")

if outro_btn and finals_exist:
    import subprocess, traceback as _tb3
    try:
        for part, final_path, complete_path in [
            (1, FINAL1, COMPLETE1),
            (2, FINAL2, COMPLETE2),
        ]:
            if not os.path.exists(OUTRO_VIDEO):
                st.error(f"Outro not found: {OUTRO_VIDEO}")
                break
            with st.spinner(f"Appending outro to Part {part}..."):
                result = subprocess.run(
                    ["ffmpeg", "-y",
                     "-i", final_path, "-i", OUTRO_VIDEO,
                     "-filter_complex",
                     "[0:v]scale=720:1280,setsar=1,fps=30[v0];"
                     "[0:a]aresample=44100[a0];"
                     "[1:v]scale=720:1280,setsar=1,fps=30[v1];"
                     "[1:a]aresample=44100[a1];"
                     "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
                     "-map", "[v]", "-map", "[a]",
                     "-c:v", "libx264", "-c:a", "aac", complete_path],
                    capture_output=True, text=True
                )
            if result.returncode != 0:
                st.error(f"Part {part} ffmpeg failed:")
                st.code(result.stderr, language=None)
                break
            st.success(f"Part {part} done → {complete_path}")
        else:
            st.rerun()
    except Exception as e:
        st.error(f"Append outro failed: {e}")
        st.code("".join(_tb3.format_exception(type(e), e, e.__traceback__)), language=None)

if complete_exist:
    c1, c2 = st.columns(2)
    with c1:
        with open(COMPLETE1, "rb") as f:
            st.download_button("Download Complete Part 1", f.read(),
                               file_name=f"rashifal_{date_str}_part1_complete.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        with open(COMPLETE2, "rb") as f:
            st.download_button("Download Complete Part 2", f.read(),
                               file_name=f"rashifal_{date_str}_part2_complete.mp4",
                               mime="video/mp4", use_container_width=True)

st.divider()

# ── STEP 7: Add Background Music ──────────────────────────────────────────────
st.subheader("Step 7 — Add Background Music")

BG_MUSIC  = os.path.join(os.path.dirname(__file__), "assets", "bg_music.mp3")
BG_VOLUME = 0.12
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "astrokiran_logo.png")

WITH_BG1 = os.path.join(_TMP, f"rashifal_{date_str}_part1_withbg.mp4")
WITH_BG2 = os.path.join(_TMP, f"rashifal_{date_str}_part2_withbg.mp4")

withbg_exist = os.path.exists(WITH_BG1) and os.path.exists(WITH_BG2)

col_bg_left, col_bg_right = st.columns([1, 2])
with col_bg_left:
    bg_volume = st.slider("Background music volume", min_value=0.0, max_value=1.0,
                          value=BG_VOLUME, step=0.01, format="%.2f")
    bg_btn = st.button("Add Background Music", type="primary",
                       disabled=not complete_exist,
                       use_container_width=True)
    if not complete_exist:
        st.caption("Complete Step 6 first.")

log_box_bg = col_bg_right.empty()

if bg_btn and complete_exist:
    import subprocess, traceback as _tb4
    from datetime import datetime as _dt
    if not os.path.exists(BG_MUSIC):
        col_bg_left.error(f"Background music not found: {BG_MUSIC}")
    elif not os.path.exists(LOGO_PATH):
        col_bg_left.error(f"Logo not found: {LOGO_PATH}")
    else:
        _d = _dt.strptime(date_str, "%Y-%m-%d")
        date_display = f"{_d.day} {_d.strftime('%B %Y')}"  # e.g. "2 March 2026"
        date_esc = date_display.replace(" ", "\\ ")       # ffmpeg filter escaping
        FONT_FILE = os.path.join(os.path.dirname(__file__), "fonts", "Arial-Bold.ttf")
        font_opt  = f":fontfile={FONT_FILE}" if os.path.exists(FONT_FILE) else ""
        log_lines_bg = []
        try:
            failed = False
            for part, complete_path, withbg_path in [
                (1, COMPLETE1, WITH_BG1),
                (2, COMPLETE2, WITH_BG2),
            ]:
                log_lines_bg.append(f"=== Part {part} ===")
                log_box_bg.code("\n".join(log_lines_bg), language=None)
                proc = subprocess.Popen(
                    ["ffmpeg", "-y",
                     "-i", complete_path, "-i", BG_MUSIC, "-i", LOGO_PATH,
                     "-filter_complex",
                     f"[1:a]volume={bg_volume},aloop=loop=-1:size=2000000000[bg];"
                     "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a];"
                     "[2:v]scale=120:-1[logo];"
                     "[0:v][logo]overlay=W-w-20:H-h-20[ov];"
                     f"[ov]drawtext=text={date_esc}{font_opt}"
                     ":fontsize=36:fontcolor=white"
                     ":x=(w-tw)/2:y=h/2+115"
                     ":box=1:boxcolor=black@0.55:boxborderw=8[v]",
                     "-map", "[v]", "-map", "[a]",
                     "-c:v", "libx264", "-c:a", "aac", withbg_path],
                    stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True
                )
                for line in proc.stderr:
                    log_lines_bg.append(line.rstrip())
                    log_box_bg.code("\n".join(log_lines_bg[-40:]), language=None)
                proc.wait()
                if proc.returncode != 0:
                    col_bg_left.error(f"Part {part} ffmpeg failed (see log)")
                    failed = True
                    break
                log_lines_bg.append(f"✓ Saved → {withbg_path}")
                log_box_bg.code("\n".join(log_lines_bg), language=None)
            if not failed:
                st.rerun()
        except Exception as e:
            col_bg_left.error(f"Background music failed: {e}")
            log_box_bg.code("".join(_tb4.format_exception(type(e), e, e.__traceback__)), language=None)

if withbg_exist:
    c1, c2 = st.columns(2)
    with c1:
        with open(WITH_BG1, "rb") as f:
            st.download_button("Download Part 1 (Final)", f.read(),
                               file_name=f"rashifal_{date_str}_part1_withbg.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        with open(WITH_BG2, "rb") as f:
            st.download_button("Download Part 2 (Final)", f.read(),
                               file_name=f"rashifal_{date_str}_part2_withbg.mp4",
                               mime="video/mp4", use_container_width=True)

st.divider()

# ── STEP 8: Split Screen (Rashifal top / Gameplay bottom) ─────────────────────
st.subheader("Step 8 — Split Screen")

GAMEPLAY_VIDEO = os.path.join(os.path.dirname(__file__), "assets", "gameplay.mp4")
SPLIT1 = os.path.join(_TMP, f"rashifal_{date_str}_part1_split.mp4")
SPLIT2 = os.path.join(_TMP, f"rashifal_{date_str}_part2_split.mp4")

split_exist = os.path.exists(SPLIT1) and os.path.exists(SPLIT2)

col_sp_left, col_sp_right = st.columns([1, 2])
with col_sp_left:
    gameplay_path = st.text_input("Gameplay video path", value=GAMEPLAY_VIDEO)
    split_btn = st.button("Generate Split Screen", type="primary",
                          disabled=not withbg_exist,
                          use_container_width=True)
    if not withbg_exist:
        st.caption("Complete Step 7 first.")

log_box_split = col_sp_right.empty()

if split_btn and withbg_exist:
    import subprocess, traceback as _tb5
    if not os.path.exists(gameplay_path):
        col_sp_left.error(f"Gameplay video not found: {gameplay_path}")
    else:
        log_lines_split = []
        try:
            failed = False
            for part, withbg_path, split_path in [
                (1, WITH_BG1, SPLIT1),
                (2, WITH_BG2, SPLIT2),
            ]:
                log_lines_split.append(f"=== Part {part} ===")
                log_box_split.code("\n".join(log_lines_split), language=None)
                proc = subprocess.Popen(
                    ["ffmpeg", "-y",
                     "-i", withbg_path,
                     "-stream_loop", "-1", "-i", gameplay_path,
                     "-filter_complex",
                     "[0:v]scale=720:640,setsar=1[top];"
                     "[1:v]scale=720:640:force_original_aspect_ratio=increase,"
                     "crop=720:640,setsar=1[bot];"
                     "[top][bot]vstack=inputs=2[v]",
                     "-map", "[v]", "-map", "0:a",
                     "-c:v", "libx264", "-c:a", "aac",
                     "-shortest", split_path],
                    stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True
                )
                for line in proc.stderr:
                    log_lines_split.append(line.rstrip())
                    log_box_split.code("\n".join(log_lines_split[-40:]), language=None)
                proc.wait()
                if proc.returncode != 0:
                    col_sp_left.error(f"Part {part} failed (see log)")
                    failed = True
                    break
                log_lines_split.append(f"✓ Saved → {split_path}")
                log_box_split.code("\n".join(log_lines_split), language=None)
            if not failed:
                st.rerun()
        except Exception as e:
            col_sp_left.error(f"Split screen failed: {e}")
            log_box_split.code("".join(_tb5.format_exception(type(e), e, e.__traceback__)), language=None)

if split_exist:
    c1, c2 = st.columns(2)
    with c1:
        with open(SPLIT1, "rb") as f:
            st.download_button("Download Part 1 (Split Screen)", f.read(),
                               file_name=f"rashifal_{date_str}_part1_split.mp4",
                               mime="video/mp4", use_container_width=True)
    with c2:
        with open(SPLIT2, "rb") as f:
            st.download_button("Download Part 2 (Split Screen)", f.read(),
                               file_name=f"rashifal_{date_str}_part2_split.mp4",
                               mime="video/mp4", use_container_width=True)
