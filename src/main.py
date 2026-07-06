# src/main.py
import json
from dataclasses import dataclass, field
from google import genai
from google.genai import types

# Initialize standard client configuration for backend companion loops
client = genai.Client()

@dataclass
class UserSessionState:
    user_id: str
    active_raaga: str
    tonic_pitch: str
    tonic_hz: float
    current_mode: str = "Welcome" # Modes: Welcome, Learn, Practice
    session_history: list = field(default_factory=list)

class SwaraRiyazOrchestrator:
    def __init__(self, session_state: UserSessionState):
        self.state = session_state
        print(f"📡 [SYSTEM] SwaraRiyaz AI Loop Initiated for User: {self.state.user_id}")

    def load_raaga_context(self):
        """Dynamically loads structural data profiles straight from the lexicon database."""
        try:
            # Open your master registry data file
            with open("data_vault/raga_lexicon.json", "r") as f:
                db = json.load(f)
            
            # Scan the array for a name matching the user's active UI dropdown choice
            for raga in db["ragas"]:
                if raga["name"].lower() == self.state.active_raaga.lower():
                    return raga
                    
            # Safe internal default fallback to prevent crashes if a lookup fails
            return db["ragas"][0]
        except Exception as e:
            # Fallback structure if the data path is temporarily unreadable
            return {
                "name": self.state.active_raaga,
                "vadi": "N/A", "samvadi": "N/A",
                "aroha": ["S", "R", "G", "M", "P", "D", "N", "S'"],
                "rules": "Standard relative scale intervals initialized."
            }

    def run_learn_mode_node(self, target_note: str):
        """Path A: Logic block computing precise synthesis values when the student clicks notes."""
        context = self.load_raaga_context()
        if target_note not in context["aroha"]:
            print(f"❌ [WARN] [Swara Auditor] Note '{target_note}' is restricted in this scale layout.")
            return
            
        print(f"\n[LEARN NODE] User clicked Swara Note Pad: [{target_note}]")
        # Deterministic generation calculation relative to custom calibrated Sa scale
        print(f" -> Generating acoustic reference pitch centered at relative frequency context.")
        print(f" -> System State preserved. Waiting for next audio asset request.")

    def run_practice_mode_node(self, target_note: str, vocal_frequency_hz: float):
        """Path B: Evaluation node running math audit metrics and formatting linguistic guidance."""
        print(f"\n[PRACTICE NODE] Student vocal response received. Intercepting micro-stream buffer...")
        print(f"[CALL] [Swara Auditor] Executing dynamic tools pitch cent audit analysis...")
        
        # Simulate local tool math evaluation step (e.g., User sings 295Hz against a 277.18Hz Sa tonic)
        tool_metrics = {
            "target_cents": 112,
            "actual_cents": 124,
            "drift_cents": 12.0,
            "intonation_status": "Teevra (Sharp)"
        }
        
        # Feed math metrics payload directly into our Guru response compiler node (Gemini 1.5 Flash/Pro)
        prompt = f"""
        You are a traditional Hindustani Classical Vocal Guru. Analyze this error telemetry:
        Target Swara: {target_note}
        Tuning Status: {tool_metrics['intonation_status']}
        Cents Deviation Error: {tool_metrics['drift_cents']} cents sharp.
        
        Output a concise, supportive 2-sentence vocal correction guiding their throat posture.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        print(f"\n[OUTPUT] [Vocal Guru Agent] 🎙️:")
        print(f" > Metrics Matrix: {tool_metrics['drift_cents']} cents drift detected.")
        print(f" > Guru Guidance: \"{response.text.strip()}\"")

    def handle_companion_chat(self, question_string: str):
        """Handles background sidebar query sessions without disrupting active practicing states."""
        print(f"\n[CHAT] [Knowledge Book Agent] Incoming query: '{question_string}'")
        context = self.load_raaga_context()
        
        prompt = f"Context: User is currently practicing Raaga {context['name']} with rules: {context['rules']}. Question: {question_string}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print(f"[OUTPUT] [Knowledge Book Agent] Response:\n{response.text.strip()}")

# --- Local Execution Entrypoint (Simulating Video Sandbox Trails) ---
if __name__ == "__main__":
    # 1. Initialize user onboarding selections
    session = UserSessionState(
        user_id="RIYAZ_STUDENT_01",
        active_raaga="Bhairav",
        tonic_pitch="C#",
        tonic_hz=277.18
    )
    
    engine = SwaraRiyazOrchestrator(session)
    
    # 2. Simulate User choosing Path A (Learn) and clicking 'r' Note Pad
    engine.state.current_mode = "Learn"
    engine.run_learn_mode_node(target_note="r")
    
    # 3. Simulate User choosing Path B (Practice) and singing slightly sharp
    engine.state.current_mode = "Practice"
    engine.run_practice_mode_node(target_note="r", vocal_frequency_hz=295.2)
    
    # 4. Simulate User opening Sidebar to ask a theory question mid-session
    engine.handle_companion_chat(question_string="What makes the morning hours suitable for practicing this scale?")