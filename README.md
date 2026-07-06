# 🎵 SwaraRiyazAI — AI-Powered Hindustani Practice Studio

SwaraRiyazAI is an interactive multimodal musicology copilot designed to assist students of Hindustani Classical Music in mastering pitch accuracy and scale microtones (Swaras). By merging traditional classical music pedagogy with modern generative AI, a Model Context Protocol (MCP) data architecture, and custom multi-harmonic acoustic synthesis, the studio provides real-time, personalized feedback as an AI Vocal Guru.

## 🌟 Core Architecture & Features

*   **Prahar (Time-of-Day) Ambient Engine:** Real Hindustani tradition assigns specific ragas to performance hours. SwaraRiyaz adapts dynamically, morphing its color gradient band and iconography depending on the selected raga (e.g., Dawn tones for *Bhairav*, Deep Night slates for *Malkauns*).
*   **Acoustic Overtone Synthesis:** Dynamically generates reference vocal swaras with true multi-harmonic overtones and built-in tanpura drone simulations.
*   **Multimodal Vocal Drill Corridor:** Captures live audio input (or processes captured samples like `student_riyaz_mic_input.wav`), traces frequency trajectories over timeline windows, and passes the vector maps to an expert evaluation engine.
*   **Model Context Protocol Nodes:** Built with an integrated MCP architecture (`src/mcp_server.py`) to connect complex musicological contexts cleanly with generative LLM tooling.
*   **Knowledge Lexicon Vault:** References static traditional pitch data rules directly from structured JSON assets (`data_vault/raga_lexicon.json`).

---

## 🛠️ Project Structure

```text
├── data_vault/
│   └── raga_lexicon.json            # Static dataset repository for raga frameworks
├── src/
│   ├── app.py                      # Production Streamlit UI & synthesis engine
│   ├── live_guru.py                # Isolated evaluation and pitch processing hub
│   ├── main.py                     # Core business logic & state orchestrator
│   └── mcp_server.py               # Model Context Protocol service layer
├── .env                            # Environment execution variables
├── .gitignore                      # Git configuration overrides
├── docker-compose.yml              # Container orchestration layer 
├── README.md                       # Comprehensive project master documentation
└── student_riyaz_mic_input.wav     # Sample hardware test recording audio


🚀 Quickstart Installation & Deployment
Local Manual Native Launch
Install core dependencies:

Bash
pip install streamlit numpy google-genai
Configure your environmental secrets in .env:

Bash
GEMINI_API_KEY="your_api_key_here"
Launch the production UI node:

Bash
streamlit run src/app.py
Docker Containerized Deployment
To spin up the entire multimodal environment alongside the background protocol servers seamlessly:

Bash
docker-compose up --build