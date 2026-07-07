# src/mcp_server.py
import json
import math
import re
import time
from collections import defaultdict, deque

from mcp.server.fastmcp import FastMCP

app = FastMCP("swarariyaz-core-math", host="0.0.0.0", port=8000)

# --- Security: input validation constants -----------------------------------
RAGA_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z ]{0,39}$")          # letters/spaces, max 40 chars
VALID_SWARAS = {"S", "r", "R", "g", "G", "M", "M'", "P", "d", "D", "n", "N", "S'", "N_"}
MIN_VOCAL_HZ, MAX_VOCAL_HZ = 50.0, 1200.0                         # realistic human vocal range

# --- Security: simple in-memory rate limiting --------------------------------
RATE_LIMIT_CALLS = 30      # max calls
RATE_LIMIT_WINDOW = 60     # per this many seconds, per tool
_call_log = defaultdict(deque)


def _rate_limited(tool_name: str) -> bool:
    now = time.time()
    log = _call_log[tool_name]
    while log and now - log[0] > RATE_LIMIT_WINDOW:
        log.popleft()
    if len(log) >= RATE_LIMIT_CALLS:
        return True
    log.append(now)
    return False


def _load_lexicon() -> dict:
    with open("data_vault/raga_lexicon.json", "r") as f:
        return json.load(f)


@app.tool()
def get_raaga_profile(raaga_name: str) -> dict:
    """Retrieves metadata, intervals, structures, and structural constraint rules for any Raaga."""
    if _rate_limited("get_raaga_profile"):
        return {"status": "error", "message": "Rate limit exceeded. Please slow down."}

    if not isinstance(raaga_name, str) or not RAGA_NAME_RE.match(raaga_name.strip()):
        return {"status": "error", "message": "Invalid raaga name format."}

    try:
        db = _load_lexicon()
        for raga in db["ragas"]:
            if raga["name"].lower() == raaga_name.strip().lower():
                return {"status": "success", "profile": raga}
        return {"status": "error", "message": f"Raaga '{raaga_name.strip()}' not found."}
    except Exception:
        # Don't leak internal exception details (file paths, tracebacks) to the client
        return {"status": "error", "message": "Unable to load raaga data."}


@app.tool()
def evaluate_vocal_pitch(target_swara: str, observed_hz: float, tonic_sa_hz: float) -> dict:
    """
    Converts absolute vocal Hz into log-cents deviations relative to custom Sa.
    Checks accuracy thresholds against classical Just Intonation parameters.
    """
    if _rate_limited("evaluate_vocal_pitch"):
        return {"status": "error", "message": "Rate limit exceeded. Please slow down."}

    if not isinstance(target_swara, str) or target_swara not in VALID_SWARAS:
        return {"status": "error", "message": "Invalid target swara."}

    try:
        observed_hz = float(observed_hz)
        tonic_sa_hz = float(tonic_sa_hz)
    except (TypeError, ValueError):
        return {"status": "error", "message": "Frequencies must be numeric."}

    if not (MIN_VOCAL_HZ <= observed_hz <= MAX_VOCAL_HZ):
        return {"status": "error", "message": f"observed_hz out of realistic vocal range ({MIN_VOCAL_HZ}-{MAX_VOCAL_HZ} Hz)."}
    if not (MIN_VOCAL_HZ <= tonic_sa_hz <= MAX_VOCAL_HZ):
        return {"status": "error", "message": f"tonic_sa_hz out of realistic vocal range ({MIN_VOCAL_HZ}-{MAX_VOCAL_HZ} Hz)."}

    try:
        db = _load_lexicon()
        intervals = db["tuning_system"]["intervals_relative_cents"]
        if target_swara not in intervals:
            return {"status": "error", "message": f"Unknown target note '{target_swara}'"}

        actual_cents = 1200 * math.log2(observed_hz / tonic_sa_hz)
        target_cents = intervals[target_swara]

        while actual_cents < -100:
            actual_cents += 1200
        while actual_cents > 1300:
            actual_cents -= 1200

        cents_drift = actual_cents - target_cents

        status = "Perfect (Sustained)"
        if cents_drift > 12:
            status = "Teevra (Sharp)"
        elif cents_drift < -12:
            status = "Komal / Flat"

        return {
            "status": "success",
            "target_cents": target_cents,
            "actual_cents": round(actual_cents, 1),
            "drift_cents": round(cents_drift, 1),
            "intonation_status": status
        }
    except Exception:
        return {"status": "error", "message": "Unable to evaluate pitch."}


if __name__ == "__main__":
    app.run(transport="streamable-http")