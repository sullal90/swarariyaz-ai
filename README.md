# 🎵 SwaraRiyazAI: Multimodal Musicology Agent

SwaraRiyazAI is an interactive practice studio built to support the oral tradition of Hindustani Classical vocal training. It combines real-time acoustic signal processing, a standalone Model Context Protocol (MCP) server, and the official Google Agent Development Kit (ADK) to act as an on-demand AI Vocal Guru — evaluating pitch accuracy against classical raga structures and giving spoken-style corrective feedback.

---

## 🏆 Course Evaluation Matrix Alignment

| Key Course Concept | Implementation | Verification |
| :--- | :--- | :--- |
| **Agent (ADK)** | `src/main.py` | Instantiates a real `google.adk.agents.Agent`, executed through ADK's own `Runner` + `InMemorySessionService`. The agent's `tools` list includes an `McpToolset` connected directly to this project's own MCP server — when it needs exact pitch-drift numbers, it calls `evaluate_vocal_pitch` through the real MCP protocol instead of estimating in free text. `app.py` calls this agent directly (`orch.consult_guru_agent(...)`) for both the sidebar chat and practice feedback — failures raise a `GuruAgentError` with the real cause, surfaced to the user via `st.error(...)`, rather than a silent fallback string. |
| **MCP Server** | `src/mcp_server.py` | Standalone `fastmcp.FastMCP` server exposing two tools (`get_raaga_profile`, `evaluate_vocal_pitch`) over `streamable-http`, reading structured raga data from `data_vault/raga_lexicon.json`. Called both directly by the frontend and by the ADK agent via `McpToolset`. |
| **Agent Skills** | `src/live_guru.py` | `VocalPitchTrackingSkill` — a self-contained skill class with a single `execute()` entry point that turns raw microphone audio into a per-note pitch trajectory via YIN. `app.py` instantiates and calls this class directly (`_pitch_skill.execute(...)`) rather than duplicating the logic inline. |
| **Security Features** | `src/mcp_server.py` | Input validation (regex allow-list on raga names, swara whitelist), bounds-checked vocal frequency ranges, generic error responses (no internal exception/path leakage), and basic per-tool rate limiting. |
| **Deployability** | `docker-compose.yml`, `Dockerfile.mcp`, `Dockerfile.app` | Two-container topology (MCP server + Streamlit frontend), each with its own Dockerfile, wired together on the Compose network — the frontend reaches the MCP server at `http://mcp-server:8000/mcp`. Brought up with a single `docker-compose up --build`. |

Not yet implemented in this submission: Antigravity IDE workflow.

**Data integrity fix:** during testing, we found the tuning data (`data_vault/raga_lexicon.json`) was missing an entry for `N_` (lower-octave Ni) — the first note of Yaman's aroha — which caused every pitch evaluation for that raga to silently fail at the tool level. A second malformed entry (`"M G"` as one string instead of two notes) was found in Poorvi's avaroha. Both are fixed; every raga's aroha/avaroha now resolves cleanly against the tuning table (verified programmatically, not just by inspection).

---

## 🏗️ System Architecture & File Layout
```text
swarariyaz-ai/
├── data_vault/
│   └── raga_lexicon.json       # Structural raga data (aroha/avaroha, vadi/samvadi, tuning intervals)
├── src/
│   ├── app.py                  # Streamlit practice studio UI
│   ├── main.py                 # ADK Agent + Runner orchestration, wired to the MCP server via McpToolset
│   ├── mcp_server.py           # Standalone MCP server (raga lookup + pitch evaluation tools)
│   ├── live_guru.py            # VocalPitchTrackingSkill — standalone pitch-analysis skill class
│   └── pitch_detection.py      # YIN pitch detection (shared by app.py and live_guru.py)
├── .env                        # Local environment variables (API keys) — not committed
├── docker-compose.yml          # Container orchestration for MCP server + frontend
├── Dockerfile.mcp              # MCP server container build
├── Dockerfile.app              # Streamlit frontend container build
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quickstart

### Docker Compose (recommended)
Brings up both the MCP server and the Streamlit frontend together:
```bash
docker-compose up --build
```
Then open **http://localhost:8501** in your browser.

### Local development
```bash
pip install -r requirements.txt

# in one terminal — start the MCP server
python src/mcp_server.py

# in another terminal — start the UI
streamlit run src/app.py
```

Set your Gemini API key before running either path:
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

> Note: for local (non-Docker) development, `main.py` connects to the MCP server at `http://localhost:8000/mcp` by default — make sure `python src/mcp_server.py` is running before using the guru chat feature in the app.

---

## 🎼 Core Features

- **Prahar (time-of-day) ambient engine** — the interface's color gradient and iconography shift based on the traditional performance time of the selected raga (dawn tones for Bhairav, deep night for Malkauns, etc.), reflecting real Hindustani performance conventions rather than arbitrary theming.
- **Acoustic overtone synthesis** — reference swara playback and tanpura drone are synthesized with multi-harmonic overtones rather than flat sine tones.
- **YIN-based vocal pitch evaluation** — records a practice take, splits it into one segment per expected note, and runs the YIN algorithm (de Cheveigne & Kawahara) on each to get a real fundamental-frequency estimate, then scores drift in cents against the raga's expected intervals. Segments with no confident pitch (silence, breath, noise) are reported honestly rather than papered over with a guessed value.
- **Raga-aware theory chat** — a sidebar assistant answers questions grounded in the currently selected raga's rules and structure.

---

## 🧹 Before Submission

- `student_riyaz_mic_input.wav` sits in the repo root and isn't referenced by any code — it looks like a leftover test recording. Worth removing (or moving into a `samples/` folder if it's meant to demonstrate the app) before final submission.

## ⚠️ Known Limitations

- YIN detection is tuned for this app's practical vocal range (`fmin=100Hz`, `fmax=650Hz`) to avoid a specific false-positive we hit during testing: 60Hz electrical mains hum being picked up as a "detected pitch" during a quiet moment. This range comfortably covers the app's practice material but would need adjusting for use outside typical Hindustani vocal practice.
- Rate limiting in `mcp_server.py` is in-memory only and resets on restart — fine for a demo/capstone context, not production-grade.
- If the guru agent fails (MCP server unreachable, Gemini API error, or an empty response), the UI shows a clear `st.error(...)` with the underlying cause rather than crashing — but the underlying `GuruAgentError` doesn't yet distinguish *which* of those three causes it was, so the message is honest but not maximally specific.