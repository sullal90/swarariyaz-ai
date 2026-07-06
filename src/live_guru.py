# src/live_guru.py
import asyncio
from google import genai
from google.genai import types

client = genai.Client()

async def start_swara_riyaz_live_session():
    # 1. Establish real-time modal config constraints
    config = types.LiveConnectConfig(
        # Model responds back natively with an expressive speaker voice
        response_modalities=[types.LiveModality.AUDIO], 
        system_instruction=(
            "You are an expert Hindustani Classical Vocal Guru. Listen to the student's sargam practice. "
            "Use the 'evaluate_vocal_pitch' tool via the local MCP server to verify their microtonal precision "
            "relative to their custom selected Sa tonic frequency baseline."
        ),
        # Expose your running FastMCP tool logic directly to the streaming audio pipeline
        tools=[{
            "function_declarations": [{
                "name": "evaluate_vocal_pitch",
                "description": "Calculates the exact relative log-cents drift from the custom Sa frequency baseline.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "target_swara": {"type": "STRING"},
                        "observed_hz": {"type": "NUMBER"},
                        "tonic_sa_hz": {"type": "NUMBER"}
                    },
                    "required": ["target_swara", "observed_hz", "tonic_sa_hz"]
                }
            }]
        }]
    )

    # 2. Open the low-latency stateful WebSocket connection
    # Using the current high-performance live multimodal audio streaming model
    active_live_model = "gemini-3.1-flash-live-preview"
    
    print(f"📡 Establishing bi-directional WSS stream to: {active_live_model}")
    async with client.aio.live.connect(model=active_live_model, config=config) as session:
        print("[SUCCESS] SwaraRiyaz AI Live Multi-Modal Voice Session started.")
        print(" -> Listening for raw 16kHz microphone PCM audio buffer input...")
        
        # This persistent state loop handles incoming audio responses and maps tool executions asynchronously
        async for response in session.receive():
            if response.tool_call:
                for function_call in response.tool_call.function_calls:
                    print(f"\n⚡ [LIVE TOOL TRIGGERED]: {function_call.name}")
                    # WebSockets intercept the audio inflection point and hand parameters down to your math engine
                    
if __name__ == "__main__":
    # Run the asynchronous websocket listener loop
    asyncio.run(start_swara_riyaz_live_session())