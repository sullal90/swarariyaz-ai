# src/mcp_server.py
import json
import math
# CHANGE THIS LINE: Import FastMCP instead of Server
from mcp.server.fastmcp import FastMCP

# CHANGE THIS LINE: Initialize app using FastMCP
app = FastMCP("swarariyaz-core-math")

@app.tool()
def get_raaga_profile(raaga_name: str) -> dict:
    """Retrieves metadata, intervals, structures, and structural constraint rules for any Raaga."""
    try:
        with open("data_vault/raga_lexicon.json", "r") as f:
            db = json.load(f)
        for raga in db["ragas"]:
            if raga["name"].lower() == raaga_name.lower():
                return {"status": "success", "profile": raga}
        return {"status": "error", "message": f"Raaga '{raaga_name}' not found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.tool()
def evaluate_vocal_pitch(target_swara: str, observed_hz: float, tonic_sa_hz: float) -> dict:
    """
    Converts absolute vocal Hz into log-cents deviations relative to custom Sa.
    Checks accuracy thresholds against classical Just Intonation parameters.
    """
    if observed_hz <= 0 or tonic_sa_hz <= 0:
        return {"status": "error", "message": "Invalid frequency metrics provided."}
        
    try:
        with open("data_vault/raga_lexicon.json", "r") as f:
            db = json.load(f)
            
        intervals = db["tuning_system"]["intervals_relative_cents"]
        if target_swara not in intervals:
            return {"status": "error", "message": f"Unknown target note '{target_swara}'"}
            
        # 1. Calculate actual observed cents from user's custom Sa baseline
        actual_cents = 1200 * math.log2(observed_hz / tonic_sa_hz)
        target_cents = intervals[target_swara]
        
        # Adjust for octave variances if user sings higher/lower than base tonic range
        while actual_cents < -100: actual_cents += 1200
        while actual_cents > 1300: actual_cents -= 1200
        
        cents_drift = actual_cents - target_cents
        
        # 2. Assign performance index categorization
        status = "Perfect (Sustained)"
        if cents_drift > 12: status = "Teevra (Sharp)"
        elif cents_drift < -12: status = "Komal / Flat"
        
        return {
            "status": "success",
            "target_cents": target_cents,
            "actual_cents": round(actual_cents, 1),
            "drift_cents": round(cents_drift, 1),
            "intonation_status": status
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    app.run()