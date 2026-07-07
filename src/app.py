# src/app.py
import streamlit as st
import numpy as np
import io
import wave
from google import genai
from main import UserSessionState, SwaraRiyazOrchestrator
from pitch_detection import analyze_pitch_trajectory

st.set_page_config(
    page_title="SwaraRiyaz — Hindustani Practice Studio",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    client = genai.Client()
except Exception:
    client = None

# ---------------------------------------------------------------------------
# PRAHAR (TIME-OF-DAY) MAP — real Hindustani tradition assigns each raga a
# performance time. We use that as the interface's one signature move: the
# ambient gradient + icon shift with whatever raga you're actually practicing,
# rather than being a fixed decoration.
# ---------------------------------------------------------------------------
PRAHAR = {
    "Bhairav":        {"label": "Dawn",       "icon": "🌅", "grad": ("#2b2140", "#c98a4b")},
    "Ahir Bhairav":   {"label": "Morning",    "icon": "🌤️", "grad": ("#2b2140", "#d9a86c")},
    "Todi":           {"label": "Late Morning","icon": "☀️", "grad": ("#241c38", "#d4af6a")},
    "Bhairavi":       {"label": "Morning",    "icon": "🌤️", "grad": ("#2b2140", "#d9a86c")},
    "Jaunpuri":       {"label": "Late Night", "icon": "🌌", "grad": ("#161221", "#4a3f6b")},
    "Durga":          {"label": "Evening",    "icon": "🌆", "grad": ("#241a33", "#8a5a7a")},
    "Bageshree":      {"label": "Night",      "icon": "🌙", "grad": ("#181428", "#5a4a8a")},
    "Malkauns":       {"label": "Deep Night", "icon": "🌑", "grad": ("#12101c", "#3d3560")},
    "Bhupali":        {"label": "Evening",    "icon": "🌆", "grad": ("#241a33", "#c9a24b")},
    "Kafi":           {"label": "Night",      "icon": "🌙", "grad": ("#181428", "#6a5a9a")},
    "Khamaj":         {"label": "Night",      "icon": "🌙", "grad": ("#181428", "#8a5a7a")},
    "Marwa":          {"label": "Dusk",       "icon": "🌇", "grad": ("#2b1a2e", "#a8462e")},
    "Poorvi":         {"label": "Dusk",       "icon": "🌇", "grad": ("#2b1a2e", "#a8462e")},
    "Yaman":          {"label": "Evening",    "icon": "🌆", "grad": ("#241a33", "#c9a24b")},
    "Dhani":          {"label": "Evening",    "icon": "🌆", "grad": ("#241a33", "#8a5a7a")},
    "Darbari Kanada": {"label": "Deep Night", "icon": "🌑", "grad": ("#12101c", "#3d3560")},
}
RAGA_LIST = list(PRAHAR.keys())
HZ_MAP = {"A#": 233.08, "B": 246.94, "C": 261.63, "C#": 277.18, "D": 293.66}

TANPURA_MARK = """
<svg width="72" height="72" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="goldFade" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#e8c77a"/>
<stop offset="100%" stop-color="#a8823f"/>
</linearGradient>
</defs>
<g transform="translate(20,20)" fill="none" stroke="url(#goldFade)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
<ellipse cx="60" cy="145" rx="52" ry="38"/>
<path d="M60 107 C 58 86, 60 36, 66 10"/>
<path d="M66 10 C 88 5, 106 8, 111 19 C 115 28, 97 31, 79 26 C 70 23, 66 16, 66 10 Z"/>
<circle cx="97" cy="13" r="4"/>
<circle cx="107" cy="24" r="4"/>
<circle cx="86" cy="24" r="4"/>
<path d="M60 145 C 60 113, 63 55, 66 13" stroke-width="1" opacity="0.55"/>
<path d="M53 145 C 55 111, 58 53, 63 11" stroke-width="1" opacity="0.4"/>
<path d="M67 145 C 65 113, 64 55, 66 15" stroke-width="1" opacity="0.4"/>
<ellipse cx="60" cy="145" rx="27" ry="18" stroke-width="1" opacity="0.5"/>
</g>
</svg>
"""

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
if "orchestrator" not in st.session_state:
    st.session_state.state_obj = UserSessionState(
        user_id="RIYAZ_STUDENT_01", active_raaga="Yaman", tonic_pitch="C#", tonic_hz=277.18
    )
    st.session_state.orchestrator = SwaraRiyazOrchestrator(st.session_state.state_obj)
    st.session_state.chat_history = []
    st.session_state.active_audio_signal = None
    st.session_state.live_guru_text = None
    st.session_state.recorded_trajectory = None

orch = st.session_state.orchestrator
prahar = PRAHAR[orch.state.active_raaga]

# ---------------------------------------------------------------------------
# THEME — one accent (brass gold), one signature (prahar gradient), quiet rest
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {{ background-color: #161221; color: #f2ece1; }}
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* Prahar ambient band — the one signature element, driven by the raga */
    .prahar-band {{
        background: linear-gradient(90deg, {prahar['grad'][0]} 0%, {prahar['grad'][1]} 100%);
        height: 6px;
        border-radius: 4px;
        margin-bottom: 18px;
        opacity: 0.85;
    }}

    h1 {{
        font-family: 'Fraunces', serif !important;
        font-weight: 600 !important;
        font-size: 2.6rem !important;
        color: #f2ece1 !important;
        margin-bottom: 0.1rem !important;
    }}
    .raga-caption {{
        font-family: 'Inter', sans-serif;
        color: #9c93ad;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }}
    .raga-caption b {{ color: #c9a24b; font-weight: 600; }}

    /* Sidebar */
    [data-testid="stSidebarContent"] {{
        background-color: #1a1526;
        border-right: 1px solid rgba(201, 162, 75, 0.15);
    }}
    [data-testid="stSidebarContent"] h3 {{
        font-family: 'Fraunces', serif !important;
        color: #c9a24b !important;
        font-weight: 600 !important;
    }}
    [data-testid="stSidebarContent"] {{
        background-image:
            radial-gradient(circle at 90% 95%, rgba(201,162,75,0.06) 0%, transparent 22%),
            radial-gradient(circle at 90% 95%, rgba(201,162,75,0.05) 0%, transparent 34%),
            radial-gradient(circle at 90% 95%, rgba(201,162,75,0.04) 0%, transparent 46%);
    }}

    /* Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #211c32 !important;
        border: 1px solid rgba(201, 162, 75, 0.18) !important;
        border-radius: 14px !important;
    }}

    /* Buttons — brass tuning-peg feel */
    div.stButton > button {{
        background-color: #211c32;
        color: #c9a24b;
        border: 1px solid rgba(201, 162, 75, 0.4);
        border-radius: 999px;
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 1.05rem;
        height: 54px;
        transition: all 0.15s ease;
    }}
    div.stButton > button:hover {{
        background-color: #c9a24b;
        color: #161221;
        border-color: #c9a24b;
        box-shadow: 0 0 14px rgba(201, 162, 75, 0.35);
    }}
    div.stButton > button[kind="primary"] {{
        background-color: #a8462e;
        color: #f2ece1;
        border: none;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #c9552f;
        box-shadow: 0 0 14px rgba(168, 70, 46, 0.4);
    }}

    /* Tabs */
    button[data-baseweb="tab"] {{
        font-family: 'Fraunces', serif;
        font-size: 1.05rem;
        color: #9c93ad;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #c9a24b !important;
    }}

    /* Data / Hz readouts */
    .hz-mono {{
        font-family: 'JetBrains Mono', monospace;
        color: #9c93ad;
        font-size: 0.85rem;
    }}

    /* Metrics */
    [data-testid="stMetricValue"] {{
        font-family: 'Fraunces', serif !important;
        color: #c9a24b !important;
    }}

    code {{
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #12101c !important;
        color: #d9a86c !important;
        border: 1px solid rgba(201, 162, 75, 0.2) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# AUDIO SYNTHESIS
# ---------------------------------------------------------------------------
def synthesize_vocal_swara(frequency_hz, duration=1.5, sample_rate=22050):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave_data = (
        1.0 * np.sin(2 * np.pi * frequency_hz * t)
        + 0.5 * np.sin(2 * np.pi * (2 * frequency_hz) * t)
        + 0.3 * np.sin(2 * np.pi * (3 * frequency_hz) * t)
        + 0.1 * np.sin(2 * np.pi * (4 * frequency_hz) * t)
    )
    wave_data = wave_data / np.max(np.abs(wave_data))
    envelope = np.ones_like(wave_data)
    fade_len = int(sample_rate * 0.15)
    envelope[:fade_len] = np.linspace(0.0, 1.0, fade_len)
    envelope[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
    return (wave_data * envelope * 0.4).astype(np.float32)


def synthesize_tanpura_drone(base_hz, duration=4.0, sample_rate=22050):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    pa_hz = base_hz * 1.5
    sa_low = base_hz * 0.5
    drone = (
        0.4 * np.sin(2 * np.pi * pa_hz * t)
        + 0.5 * np.sin(2 * np.pi * base_hz * t)
        + 0.6 * np.sin(2 * np.pi * sa_low * t)
    )
    return ((drone / np.max(np.abs(drone))) * 0.35).astype(np.float32)


def analyze_directional_pitch_trajectory(audio_bytes, focus_mode, num_notes=6):
    """
    Returns a list of per-note pitch estimates in Hz using YIN detection, one
    entry per note in the target sequence (num_notes). Entries are `None`
    where no confident pitch was found (silence, breath, noise-dominated
    chunk, or mains hum) rather than a fabricated value.

    fmin is set to 100 Hz (rather than the module default of 60 Hz) because
    this app's practice range never goes that low, and 60 Hz is exactly
    where US electrical mains hum sits — a common false-positive source when
    a chunk is otherwise quiet.
    """
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            data = wav_file.readframes(n_frames)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            return analyze_pitch_trajectory(
                samples, sample_rate, steps=num_notes, fmin=100.0, fmax=650.0
            )
    except Exception:
        return [None] * num_notes


CENTS = {
    "S": 0, "r": 112, "R": 204, "g": 316, "G": 386, "M": 498, "M'": 590,
    "P": 702, "d": 814, "D": 906, "n": 1018, "N": 1088, "S'": 1200, "N_": -112,
}

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎼 Practice Setup")

    raaga_choice = st.selectbox("Raaga", RAGA_LIST, index=RAGA_LIST.index(orch.state.active_raaga))
    if raaga_choice != orch.state.active_raaga:
        orch.state.active_raaga = raaga_choice
        st.rerun()

    pitch_choice = st.selectbox("Sa (tonic)", list(HZ_MAP.keys()),
                                 index=list(HZ_MAP.keys()).index(orch.state.tonic_pitch))
    orch.state.tonic_pitch = pitch_choice
    orch.state.tonic_hz = HZ_MAP[pitch_choice]

    raga_profile = orch.load_raaga_context()
    aroha_scale = raga_profile.get("aroha", ["S", "R", "G", "M", "P", "D", "N", "S'"])
    avaroha_scale = raga_profile.get("avaroha", ["S'", "N", "D", "P", "M", "G", "R", "S"])
    rules = raga_profile.get("rules", "Standard scale boundaries apply.")

    st.divider()
    st.caption(f"{prahar['icon']}  TRADITIONAL TIME · {prahar['label'].upper()}")
    c1, c2 = st.columns(2)
    c1.metric("Vadi", raga_profile.get("vadi", "—"))
    c2.metric("Samvadi", raga_profile.get("samvadi", "—"))
    st.caption(rules)

    if st.button("▶ Play tanpura drone", use_container_width=True):
        drone_wave = synthesize_tanpura_drone(orch.state.tonic_hz)
        st.session_state.active_audio_signal = ("Tanpura Drone", drone_wave)

    st.divider()
    with st.expander("💬 Ask about this raaga"):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        chat_input = st.chat_input("Ask about microtones...")
        if chat_input:
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            if client:
                with st.spinner("Consulting library..."):
                    prompt = (
                        f"You are an expert Hindustani Classical Musicology Professor. "
                        f"Answer accurately in 2 sentences. Context Raaga {orch.state.active_raaga}, "
                        f"Aroha: {'->'.join(aroha_scale)}, Rules: {rules}. Question: {chat_input}"
                    )
                    try:
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        reply = response.text
                    except Exception:
                        reply = "Theory lookup module active."
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

# ---------------------------------------------------------------------------
# MAIN AREA
# ---------------------------------------------------------------------------
st.markdown('<div class="prahar-band"></div>', unsafe_allow_html=True)

header_col, mark_col = st.columns([6, 1])
with header_col:
    st.title("SwaraRiyaz")
    st.markdown(
        f'<div class="raga-caption">Practicing <b>{orch.state.active_raaga}</b> '
        f'· {prahar["icon"]} traditionally sung at <b>{prahar["label"]}</b> '
        f'· Sa = {pitch_choice} ({orch.state.tonic_hz:.1f} Hz)</div>',
        unsafe_allow_html=True,
    )
with mark_col:
    st.markdown(f'<div style="text-align:right;">{TANPURA_MARK}</div>', unsafe_allow_html=True)

tab_reference, tab_drill = st.tabs(["🎹 Reference Notes", "🎙️ Practice & Evaluation"])

# --- Tab 1: reference note matrix ------------------------------------------
with tab_reference:
    st.write("Tap a swara to hear its reference pitch relative to your chosen Sa.")

    st.markdown("**↗ Aroha (ascending)**")
    aroha_cols = st.columns(len(aroha_scale))
    for i, swara in enumerate(aroha_scale):
        with aroha_cols[i]:
            if st.button(swara, key=f"aro_{swara}_{i}", use_container_width=True):
                cents = CENTS.get(swara, 0)
                target_hz = orch.state.tonic_hz * (2 ** (cents / 1200))
                st.session_state.active_audio_signal = (f"Aroha {swara}", synthesize_vocal_swara(target_hz))

    st.markdown("**↘ Avaroha (descending)**")
    avaroha_cols = st.columns(len(avaroha_scale))
    for i, swara in enumerate(avaroha_scale):
        with avaroha_cols[i]:
            if st.button(swara, key=f"ava_{swara}_{i}", use_container_width=True):
                cents = CENTS.get(swara, 0)
                target_hz = orch.state.tonic_hz * (2 ** (cents / 1200))
                st.session_state.active_audio_signal = (f"Avaroha {swara}", synthesize_vocal_swara(target_hz))

# --- Tab 2: recording + evaluation ------------------------------------------
with tab_drill:
    drill_direction = st.radio(
        "Practice direction", ["Ascending (Aroha)", "Descending (Avaroha)"], horizontal=True
    )
    target_sequence = aroha_scale if "Ascending" in drill_direction else avaroha_scale
    st.code(" → ".join(target_sequence), language=None)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("**1. Record**")
        audio_value = st.audio_input("Sing the sequence above")

        if audio_value is not None:
            if st.button("Evaluate my recording", type="primary", use_container_width=True):
                audio_bytes = audio_value.read()
                with st.spinner("Analyzing pitch trajectory..."):
                    trajectory = analyze_directional_pitch_trajectory(
                        audio_bytes, drill_direction.upper(), num_notes=len(target_sequence)
                    )
                    st.session_state.recorded_trajectory = trajectory

                    detected_count = sum(1 for hz in trajectory if hz is not None)
                    if detected_count == 0:
                        st.session_state.live_guru_text = None
                        st.warning(
                            "Couldn't detect a clear pitch in that recording — "
                            "try again a little closer to the mic, and make sure "
                            "there's minimal background noise."
                        )
                    else:
                        # Represent undetected chunks explicitly rather than as
                        # a bare `None`, so the prompt (and the model) treat
                        # them as missing data, not a value to reason about.
                        readable_trajectory = [
                            f"{hz} Hz" if hz is not None else "no clear pitch detected"
                            for hz in trajectory
                        ]

                        if detected_count < len(trajectory):
                            st.info(
                                f"Detected pitch in {detected_count} of {len(trajectory)} "
                                f"segments — the rest may have been too quiet or noisy."
                            )

                        if client:
                            prompt = f"""
                            You are an expert Hindustani Classical Vocal Guru evaluating a student's
                            isolated practice recording. They are singing the {drill_direction} scale
                            of Raaga {orch.state.active_raaga} relative to a base Sa of {orch.state.tonic_hz} Hz.

                            Expected swara order: {', '.join(target_sequence)}
                            Parsed frequency sequence from their recording, in order: {', '.join(readable_trajectory)}.
                            Some segments may say "no clear pitch detected" — treat those as missing
                            data (e.g. a breath or gap), not as an intonation error.

                            Evaluate alignment directly:
                            - Note whether the sequence climbs/falls smoothly along the target intervals.
                            - Point out which swaras are sharp (Teevra) or flat (Komal).
                            Give a precise, encouraging 2-sentence lesson.
                            """
                            try:
                                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                                st.session_state.live_guru_text = response.text.strip()
                            except Exception:
                                st.session_state.live_guru_text = (
                                    "Your steady breath on Sa is strong. Keep the vocal column centered as you expand."
                                )

    with right:
        st.markdown("**2. Feedback**")
        if st.session_state.live_guru_text:
            with st.container(border=True):
                st.markdown(f"🎙️ *{st.session_state.live_guru_text}*")
                display_trajectory = [
                    hz if hz is not None else "—" for hz in (st.session_state.recorded_trajectory or [])
                ]
                st.markdown(
                    f'<span class="hz-mono">Tracked pitch: {display_trajectory} Hz</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Record and evaluate a take to see feedback here.")

# ---------------------------------------------------------------------------
# AUDIO PLAYBACK
# ---------------------------------------------------------------------------
if st.session_state.active_audio_signal is not None:
    label, signal = st.session_state.active_audio_signal
    st.audio(signal, sample_rate=22050, autoplay=True)
    st.session_state.active_audio_signal = None