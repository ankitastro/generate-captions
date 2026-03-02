import os, sys, wave as wav_mod, time, json, sqlite3
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
WAV1, WAV2       = "/tmp/rashi_p1.wav", "/tmp/rashi_p2.wav"
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

उदाहरण (इसी लंबाई में लिखो):
मेष  Expense Alert: आज अचानक कोई बड़ा खर्चा आ सकता है। दोस्तों या परिवार के चक्कर में आज आपका बजट पूरी तरह हिल सकता है।
वृषभ  आज आप दिन भर आराम करना चाहेंगे, लेकिन अचानक कोई मेहमान या काम निकल आने से पूरा आराम खराब हो सकता है। चिड़ें नहीं।
मिथुन  Danger Zone: आज कोई छोटी सी गलतफहमी की वजह से पार्टनर या दोस्तों के साथ प्लान कैंसिल हो सकता है।

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
    st.subheader("Previous Sessions")
    past = db_list_dates()
    if past:
        for row in past:
            audio_info = f" · {row[1]:.0f}s+{row[2]:.0f}s" if row[1] else ""
            st.caption(f"📅 {row[0]}{audio_info}")
    else:
        st.caption("No saved sessions yet.")

# ── Session state init ────────────────────────────────────────────────────────
for key in ["text_p1", "text_p2", "dur1", "dur2", "words1", "words2", "loaded_date"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Auto-load from DB when date changes
if st.session_state.loaded_date != date_str:
    session = db_load_session(date_str)
    if session:
        st.session_state.text_p1 = session["text_p1"]
        st.session_state.text_p2 = session["text_p2"]
        st.session_state.dur1    = session["dur1"]
        st.session_state.dur2    = session["dur2"]
    else:
        st.session_state.text_p1 = None
        st.session_state.text_p2 = None
        st.session_state.dur1    = None
        st.session_state.dur2    = None
    st.session_state.words1 = db_load_timestamps(date_str, 1)
    st.session_state.words2 = db_load_timestamps(date_str, 2)
    st.session_state.loaded_date = date_str

text_ready       = bool(st.session_state.text_p1 and st.session_state.text_p2)
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
        edited_p1 = st.text_area("", value=st.session_state.text_p1,
                                  height=280, key="edit_p1", label_visibility="collapsed")
        if edited_p1 != st.session_state.text_p1:
            st.session_state.text_p1 = edited_p1
            db_save_session(date_str, text_p1=edited_p1)
    with c2:
        st.caption("Part 2 — तुला → मीन")
        edited_p2 = st.text_area("", value=st.session_state.text_p2,
                                  height=280, key="edit_p2", label_visibility="collapsed")
        if edited_p2 != st.session_state.text_p2:
            st.session_state.text_p2 = edited_p2
            db_save_session(date_str, text_p2=edited_p2)

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
            dur1 = generate_tts(st.session_state.text_p1, WAV1)
        with st.spinner("Generating TTS for Part 2 (~30s)..."):
            dur2 = generate_tts(st.session_state.text_p2, WAV2)
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

OUT1 = f"/tmp/rashifal_{date_str}_part1.mp4"
OUT2 = f"/tmp/rashifal_{date_str}_part2.mp4"

col_btn4, _ = st.columns([1, 4])
with col_btn4:
    build_btn = st.button("Build Videos", type="primary",
                           disabled=not timestamps_ready, use_container_width=True)

if not timestamps_ready:
    st.caption("Complete Step 3 first.")

if build_btn and timestamps_ready:
    _, _, _, _, _, _, build_video_fn, *_rest = _load_libs()
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
