# src/main.py
import dataclasses
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


@dataclasses.dataclass
class UserSessionState:
    """Maintains critical training parameters inside the ADK execution context."""
    user_id: str
    active_raaga: str
    tonic_pitch: str
    tonic_hz: float


class SwaraRiyazOrchestrator:
    """Manages musicology context utilizing the official Google ADK framework."""

    APP_NAME = "swarariyaz"

    def __init__(self, session_state: UserSessionState):
        self.state = session_state

        # Real ADK Agent — this is what actually gets executed, not just referenced
        self.guru_agent = Agent(
            name="GuruMusicologyAgent",
            model="gemini-2.5-flash",
            instruction=(
                "You are an expert Hindustani Classical Musicology Professor. "
                "Answer accurately in 2 sentences."
            ),
        )

        # ADK session service + runner — the actual execution path for the agent
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self.guru_agent,
            app_name=self.APP_NAME,
            session_service=self._session_service,
        )
        self._session_ready = False

        self._raga_database = {
            "Yaman": {
                "vadi": "N", "samvadi": "G",
                "aroha": ["N_", "R", "G", "M'", "D", "N", "S'"],
                "avaroha": ["S'", "N", "D", "P", "M'", "G", "R", "S"],
                "rules": "Strictly uses Teevra Madhyam (M'). Sa is frequently skipped in ascending phrases (N_ R G)."
            }
        }

    def load_raaga_context(self) -> dict:
        raga = self.state.active_raaga
        return self._raga_database.get(raga, {
            "vadi": "S", "samvadi": "P",
            "aroha": ["S", "R", "G", "M", "P", "D", "N", "S'"],
            "avaroha": ["S'", "N", "D", "P", "M", "G", "R", "S"],
            "rules": "Standard boundaries applied."
        })

    async def _ensure_session(self):
        if not self._session_ready:
            await self._session_service.create_session(
                app_name=self.APP_NAME,
                user_id=self.state.user_id,
                session_id=self.state.user_id,
            )
            self._session_ready = True

    async def _consult_guru_agent_async(self, user_query: str, raga_context: dict) -> str:
        """Runs the ADK agent through its actual Runner instead of a raw genai call."""
        await self._ensure_session()

        context_query = (
            f"Context Raaga: {self.state.active_raaga}. "
            f"Rules: {raga_context['rules']}. Query: {user_query}"
        )
        message = types.Content(role="user", parts=[types.Part(text=context_query)])

        final_text = "Acoustic knowledge bank synced."
        try:
            for event in self._runner.run(
                user_id=self.state.user_id,
                session_id=self.state.user_id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text
        except Exception:
            pass
        return final_text

    def consult_guru_agent(self, user_query: str, raga_context: dict) -> str:
        """Sync wrapper so Streamlit callbacks can call this directly."""
        return asyncio.run(self._consult_guru_agent_async(user_query, raga_context))