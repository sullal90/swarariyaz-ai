# 🎵 SwaraRiyazAI: Multimodal Musicology Agent

SwaraRiyazAI is an interactive practice studio built to support the oral tradition of Hindustani Classical vocal training. It combines real-time acoustic signal processing, a standalone Model Context Protocol (MCP) server, and the official Google Agent Development Kit (ADK) to act as an on-demand AI Vocal Guru — evaluating pitch accuracy against classical raga structures and giving spoken-style corrective feedback.

---

## 🏆 Course Evaluation Matrix Alignment

| Key Course Concept | Implementation | Verification |
| :--- | :--- | :--- |
| **Agent (ADK)** | `src/main.py` | Instantiates a real `google.adk.agents.Agent`, and executes it through ADK's own `Runner` + `InMemorySessionService` — the agent is actually run through the framework, not just referenced. |
| **MCP Server** | `src/mcp_server.py` | Standalone `fastmcp.FastMCP` server exposing two tools (`get_raaga_profile`, `evaluate_vocal_pitch`) that read structured raga data from `data_vault/raga_lexicon.json`. |
| **Agent Skills** | `src/live_guru.py` | `VocalPitchTrackingSkill` — a self-contained, named skill class with a single `execute()` entry point encapsulating pitch-trajectory analysis. *Not yet called through ADK's own skill/tool registration — `app.py` currently invokes the equivalent logic directly rather than through this class.* |
| **Security Features** | `src/mcp_server.py` | Input validation (regex allow-list on raga names, swara whitelist), bounds-checked vocal frequency ranges, generic error responses (no internal exception/path leakage), and basic per-tool rate limiting. |
| **Deployability** | `docker-compose.yml` | Two-service container topology (MCP server + Streamlit frontend) brought up with a single command. |

Not yet implemented in this submission: Antigravity IDE workflow.

---

## 🏗️ System Architecture & File Layout
```text
swarariyaz-ai/
├── data_vault/
│   └── raga_lexicon.json       # Structural raga data (aroha/avaroha, vadi/samvadi, tuning intervals)
├── src/
│   ├── app.py                  # Streamlit practice studio UI
│   ├── main.py                 # ADK Agent + Runner orchestration
│   ├── mcp_server.py           # Standalone MCP server (raga lookup + pitch evaluation tools)
│   └── live_guru.py            # VocalPitchTrackingSkill — standalone pitch-analysis skill class
├── .env                        # Local environment variables (API keys) — not committed
├── docker-compose.yml          # Container orchestration for MCP server + frontend
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
export GEMINI_API_KEY="your_api_key_here"
```

---

## 🎼 Core Features

- **Prahar (time-of-day) ambient engine** — the interface's color gradient and iconography shift based on the traditional performance time of the selected raga (dawn tones for Bhairav, deep night for Malkauns, etc.), reflecting real Hindustani performance conventions rather than arbitrary theming.
- **Acoustic overtone synthesis** — reference swara playback and tanpura drone are synthesized with multi-harmonic overtones rather than flat sine tones.
- **Vocal pitch evaluation** — records a practice take, estimates pitch trajectory across the phrase, and scores drift in cents against the raga's expected intervals.
- **Raga-aware theory chat** — a sidebar assistant answers questions grounded in the currently selected raga's rules and structure.

---

## ⚠️ Known Limitations

- Pitch detection in `app.py` uses a simplified zero-crossing estimate rather than a robust algorithm (e.g. YIN/CREPE); accuracy on real microphone input may be inconsistent.
- `live_guru.py` is an early prototype for a real-time voice session and is not yet wired into the main app flow.
- Rate limiting in `mcp_server.py` is in-memory only and resets on restart — fine for a demo/capstone context, not production-grade.