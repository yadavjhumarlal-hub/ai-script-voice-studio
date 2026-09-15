import streamlit as st
import edge_tts
import asyncio
import os
import shutil
import subprocess
import tempfile

st.set_page_config(
    page_title="Edge-TTS Professional Studio",
    page_icon="🎙️",
    layout="wide"
)

# =========================================================
# PROFESSIONAL DARK UI
# =========================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #080b14 0%, #17133b 100%);
    color: #f8fafc;
    font-family: 'Segoe UI', sans-serif;
}

.studio-header {
    text-align: center;
    padding: 10px 0 22px 0;
}

.studio-title {
    font-size: 2.3rem;
    font-weight: 800;
    background: linear-gradient(90deg,#38bdf8,#818cf8,#c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.studio-subtitle {
    color: #94a3b8;
    font-size: .95rem;
}

.studio-card {
    background: rgba(30,41,59,.72);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,.35);
}

.metric-chip {
    display:inline-block;
    background:rgba(15,23,42,.85);
    border:1px solid #334155;
    border-radius:8px;
    padding:5px 12px;
    font-size:.84rem;
    color:#38bdf8;
    margin-right:7px;
    margin-top:6px;
}

.stButton>button {
    width:100%;
    background:linear-gradient(90deg,#4f46e5,#7c3aed)!important;
    color:white!important;
    font-weight:700!important;
    border:none!important;
    border-radius:12px!important;
    padding:12px!important;
}

.stDownloadButton>button {
    width:100%;
    border-radius:12px!important;
    font-weight:700!important;
}

.stTextArea textarea {
    background:#0f172a!important;
    color:#f8fafc!important;
    border:1px solid #334155!important;
    border-radius:14px!important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="studio-header">
    <div class="studio-title">🎙️ Edge-TTS Professional Studio</div>
    <div class="studio-subtitle">
        Free Neural Voice • Professional Controls • Audio Mastering
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# VOICE CATALOG
# =========================================================
voices = {
    "Hindi Male — Madhur Natural": "hi-IN-MadhurNeural",
    "Hindi Female — Swara Natural": "hi-IN-SwaraNeural",

    "Hindi Male — Deep Documentary": "hi-IN-MadhurNeural",
    "Hindi Male — Cinematic Deep": "hi-IN-MadhurNeural",
    "Hindi Male — Energetic RJ": "hi-IN-MadhurNeural",

    "Hindi Female — News": "hi-IN-SwaraNeural",
    "Hindi Female — Calm Story": "hi-IN-SwaraNeural",
    "Hindi Female — Soft Narrator": "hi-IN-SwaraNeural",

    "English Male — Guy": "en-US-GuyNeural",
    "English Female — Jenny": "en-US-JennyNeural"
}


# =========================================================
# PRESETS
# =========================================================
presets = {
    "🎙️ Natural": {
        "speed": 0,
        "pitch": 0,
        "volume": 0,
        "boost": 0
    },

    "🎬 Deep Documentary": {
        "speed": -5,
        "pitch": -12,
        "volume": 0,
        "boost": 2
    },

    "🎥 Cinematic Trailer": {
        "speed": -8,
        "pitch": -18,
        "volume": 2,
        "boost": 3
    },

    "📖 Storytelling": {
        "speed": -5,
        "pitch": -4,
        "volume": 1,
        "boost": 2
    },

    "📱 YouTube Shorts": {
        "speed": 8,
        "pitch": 2,
        "volume": 2,
        "boost": 2
    },

    "📰 News / Facts": {
        "speed": 2,
        "pitch": 0,
        "volume": 1,
        "boost": 1
    },

    "🧘 Calm Narration": {
        "speed": -10,
        "pitch": -5,
        "volume": 0,
        "boost": 1
    }
}


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("⚙️ Professional Voice Settings")

preset_name = st.sidebar.selectbox(
    "🎚️ Voice Preset",
    list(presets.keys())
)

preset = presets[preset_name]

selected_voice_name = st.sidebar.selectbox(
    "🎙️ Voice",
    list(voices.keys())
)

voice_code = voices[selected_voice_name]

st.sidebar.markdown("---")

speed = st.sidebar.slider(
    "⚡ Speed",
    -30, 30,
    preset["speed"],
    1
)

pitch = st.sidebar.slider(
    "🎚️ Pitch / Heavy",
    -24, 24,
    preset["pitch"],
    1
)

volume = st.sidebar.slider(
    "🔊 Volume",
    -20, 10,
    preset["volume"],
    1
)

boost = st.sidebar.slider(
    "🔉 Voice Boost",
    0, 6,
    preset["boost"],
    1
)

normalize = st.sidebar.checkbox(
    "🎧 Professional Normalization",
    value=True
)

st.sidebar.markdown("---")

st.sidebar.info(
    "Edge-TTS engine को बदले बिना उसके output पर "
    "professional audio processing लागू की जाती है।"
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def edge_rate(value):
    return f"{value:+d}%"


def edge_pitch(value):
    return f"{value:+d}Hz"


async def generate_edge_audio(text, voice, rate, pitch, output):
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        pitch=pitch
    )
    await communicate.save(output)


def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def master_audio(input_file, output_file, volume_db, boost_db, normalize_audio):
    """
    Professional audio finishing using FFmpeg.
    If FFmpeg is unavailable, original Edge-TTS MP3 is retained.
    """

    if not ffmpeg_available():
        shutil.copy(input_file, output_file)
        return False

    filters = []

    total_gain = volume_db + boost_db

    if total_gain != 0:
        filters.append(f"volume={total_gain}dB")

    if normalize_audio:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    filter_chain = ",".join(filters)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file
    ]

    if filter_chain:
        command += ["-af", filter_chain]

    command += [
        "-codec:a", "libmp3lame",
        "-b:a", "192k",
        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        shutil.copy(input_file, output_file)
        return False

    return True


# =========================================================
# MAIN LAYOUT
# =========================================================
col1, col2 = st.columns([1.15, 1], gap="medium")


# =========================================================
# LEFT — SCRIPT
# =========================================================
with col1:

    st.markdown(
        '<div class="studio-card">',
        unsafe_allow_html=True
    )

    st.subheader("📝 Script Console")

    text_input = st.text_area(
        "अपना Text / Script दर्ज करें",
        height=280,
        placeholder=(
            "यहाँ अपनी YouTube script, facts, कहानी, "
            "documentary या reels का text लिखें..."
        )
    )

    words = len(text_input.split()) if text_input.strip() else 0
    chars = len(text_input)

    # Approximate duration
    est_sec = round(words / 2.5) if words else 0

    st.markdown(f"""
    <div style="margin-bottom:15px">
        <span class="metric-chip">📝 अक्षर: <b>{chars}</b></span>
        <span class="metric-chip">💬 शब्द: <b>{words}</b></span>
        <span class="metric-chip">⏱️ अनुमानित: <b>~{est_sec} sec</b></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎛️ Current Settings")

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.metric("Speed", f"{speed:+d}%")

    with s2:
        st.metric("Pitch", f"{pitch:+d}Hz")

    with s3:
        st.metric("Volume", f"{volume:+d}dB")

    with s4:
        st.metric("Boost", f"{boost:+d}dB")

    generate_btn = st.button(
        "🚀 Generate Professional Audio"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# RIGHT — OUTPUT
# =========================================================
with col2:

    st.markdown(
        '<div class="studio-card">',
        unsafe_allow_html=True
    )

    st.subheader("🎧 Professional Audio Output")

    if generate_btn:

        if not text_input.strip():
            st.error("कृपया पहले Text दर्ज करें।")

        else:

            with st.spinner(
                "🎙️ Neural voice तैयार हो रही है और audio mastering चल रही है..."
            ):

                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                )

                temp_file.close()

                raw_audio = temp_file.name

                final_audio = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                )

                final_audio.close()

                final_path = final_audio.name

                try:

                    # -----------------------------------------
                    # EDGE TTS
                    # -----------------------------------------
                    asyncio.run(
                        generate_edge_audio(
                            text_input,
                            voice_code,
                            edge_rate(speed),
                            edge_pitch(pitch),
                            raw_audio
                        )
                    )

                    # -----------------------------------------
                    # PROFESSIONAL MASTERING
                    # -----------------------------------------
                    mastering_used = master_audio(
                        raw_audio,
                        final_path,
                        volume,
                        boost,
                        normalize
                    )

                    st.success(
                        "🎉 Professional Studio Audio तैयार है!"
                    )

                    if mastering_used:
                        st.caption(
                            "✅ Edge-TTS + Professional Audio Mastering"
                        )
                    else:
                        st.caption(
                            "ℹ️ Edge-TTS audio तैयार है। "
                            "Advanced mastering के लिए FFmpeg उपलब्ध नहीं मिला।"
                        )

                    st.audio(
                        final_path,
                        format="audio/mp3"
                    )

                    with open(
                        final_path,
                        "rb"
                    ) as audio_file:

                        st.download_button(
                            label="⬇️ Download Professional MP3",
                            data=audio_file,
                            file_name="edge_professional_voice.mp3",
                            mime="audio/mpeg"
                        )

                except Exception as e:

                    st.error(
                        f"❌ Audio Generation Error: {e}"
                    )

                finally:

                    try:
                        if os.path.exists(raw_audio):
                            os.remove(raw_audio)

                        if os.path.exists(final_path):
                            os.remove(final_path)

                    except Exception:
                        pass

    else:

        st.info(
            "💡 Voice चुनें → Preset चुनें → Text डालें → "
            "Generate दबाएँ।"
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div style="
text-align:center;
color:#64748b;
padding:15px;
font-size:.8rem;
">
Edge-TTS Professional Test V1 • Free Neural Voice Engine
</div>
""", unsafe_allow_html=True)
