# 🎵 SwaraRiyazAI: Multimodal Musicology Agent

SwaraRiyazAI is an interactive practice studio engineered to democratize and preserve the complex oral tradition of Hindustani Classical Vocal Training. Powered by a decoupled architecture combining advanced time-series audio signal processing, a standalone Model Context Protocol (MCP) server, and the official Google Agent Development Kit (ADK), it serves as an anytime-available automated "AI Vocal Guru."

---

## 🏆 Course Evaluation Matrix Alignment
This repository is engineered to fully satisfy the technical criteria defined in the Capstone evaluation rubrics:

| Key Course Concept | Implementation File | Technical Verification |
| :--- | :--- | :--- |
| **Agent / Multi-agent (ADK)** | `src/main.py` | Instantiates a true `google.adk.agents.Agent` instance, orchestrating pedagogical execution boundaries and setting runtime instructions. |
| **MCP Server** | `src/mcp_server.py` | Implements a robust `fastmcp.FastMCP` standalone architecture parsing contextual structures from `data_vault/raga_lexicon.json`. |
| **Agent Skills** | `src/live_guru.py` | Encapsulates the core algorithmic voice tracking processing logic inside a dedicated computational custom `VocalPitchTrackingSkill`. |
| **Security Features** | `.env` / `docker-compose.yml` | Full decoupling of sensitive application parameters, environment secret containment, and sandbox process boundary isolation. |
| **Deployability** | `docker-compose.yml` | Containerized build blueprint orchestrating multi-service networks (Frontend + MCP) with a single command line call. |

---

## 🏗️ System Architecture & File Layout
```text
swarariyaz-ai/
├── data_vault/
│   └── raga_lexicon.json       # Structural domain knowledge constraints
├── src/
│   ├── app.py                  # Responsive Streamlit studio dashboard
│   ├── main.py                 # Core Google ADK orchestration hub
│   ├── mcp_server.py           # Standalone Model Context Protocol server
│   └── live_guru.py            # Computational frequency tracking skill
├── .env                        # Isolated environment variables & API configs
├── docker-compose.yml          # Container orchestration topology
└── requirements.txt            # Production build dependencies


🚀 Quickstart Deployment
📦 Running Natively via Docker Compose
To deploy the entire multi-service ecosystem securely inside an isolated runtime container environment, execute:

Bash
docker-compose up --build
Once initialized, open your browser to http://localhost:8501 to access the interactive studio canvas.

🐍 Local Development Setup
Install Dependencies:

Bash
pip install -r requirements.txt
Launch the MCP Context Node:

Bash
python src/mcp_server.py
Run the Interactive Dashboard:

Bash
streamlit run src/app.py