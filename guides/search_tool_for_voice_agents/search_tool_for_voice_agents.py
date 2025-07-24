import os
import asyncio
import threading
import time
import io


import dotenv
import requests
import sounddevice as sd
import numpy as np
from openai import OpenAI
from zeroentropy import ZeroEntropy
from agents import Agent
from agents.mcp import MCPServerSse
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
    VoicePipelineConfig,
    TTSModelSettings,
)

# Load environment variables
dotenv.load_dotenv()

# Configuration
ZEROENTROPY_API_KEY = os.getenv("ZEROENTROPY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_URL = "https://openai-deepresearch.zeroentropy.dev/sse/"
COLLECTION_NAME = "yc_voice_agent_support"
YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"

# Audio settings
SAMPLE_RATE = 24000
CHANNELS = 1

# Prompts
SYSTEM_PROMPT = (
    "You receive transcribed user speech. "
    "Rewrite the query into a precise search, always call the search tool via MCP, "
    "fetch results, and answer in English, succinctly."
)

TTS_PROMPT = (
    "You are a helpful voice assistant who can answer any question about any YC company. "
    "Personality: Helpful and concise voice assistant. "
    "Tone: Friendly and clear. "
    "Pause naturally between points."
)

# Initialize clients
ze_client = ZeroEntropy(api_key=ZEROENTROPY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def setup_yc_data():
    """Fetch YC companies and add to ZeroEntropy collection."""
    print("Setting up YC company data...")
    
    # Create collection
    try:
        ze_client.collections.add(collection_name=COLLECTION_NAME)
        print(f"Created collection: {COLLECTION_NAME}")
    except Exception:
        print(f"Collection {COLLECTION_NAME} already exists")
    
    # Fetch companies
    try:
        response = requests.get(YC_API_URL, timeout=30)
        response.raise_for_status()
        companies = response.json()
        print(f"Fetched {len(companies)} companies")
    except Exception as e:
        print(f"Failed to fetch companies: {e}")
        return False
    
    # Add companies to collection
    success_count = 0
    for company in companies:
        try:
            slug = str(company.get('slug', ''))
            text = (
                f"{company.get('name', '')} — {company.get('one_liner', '')}\n\n"
                f"{company.get('long_description', '')}\n\n"
                f"{company.get('website', '')}\n\n"
                f"{company.get('subindustry', '')}\n\n"
                f"Stage: {company.get('stage', '')}"
            )
            metadata = {
                "batch": company.get("batch", ""),
                "list:industries": company.get("industries", []),
                "stage": company.get("stage", ""),
            }
            
            ze_client.documents.add(
                collection_name=COLLECTION_NAME,
                path=slug,
                content={"type": "text", "text": text},
                metadata=metadata
            )
            success_count += 1
        except Exception:
            continue
    
    print(f"Added {success_count} companies to collection")
    return success_count > 0


def record_enter_to_talk():
    """Record audio until Enter key is pressed."""
    print("Press ENTER to start recording, then press ENTER again to stop...")
    
    # Wait for first Enter press to start recording
    input("Press ENTER to start recording: ")
    print("🎤 Recording... Press ENTER to stop")
    
    audio_data = []
    recording = True
    
    def audio_callback(indata, frames, time, status):
        if recording:
            audio_data.append(indata.copy())
    
    # Start audio recording
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=audio_callback
    )
    
    with stream:
        # Wait for second Enter press to stop recording
        input()  # This will block until Enter is pressed
        recording = False
        print("⏹️ Recording stopped")
    
    if audio_data:
        return np.concatenate(audio_data, axis=0)
    return None


def transcribe_audio(audio_array):
    """Transcribe audio to text."""
    audio_bytes = audio_array.tobytes()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "user_input.wav"
    
    transcript = openai_client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
        response_format="text"
    )
    
    print(f"You said: {transcript.text}")
    return transcript.text


async def run_voice_assistant():
    """Main voice assistant loop."""
    print("\n🎙️ Voice Assistant")
    print("📝 Instructions:")
    print("   • Press ENTER to start recording")
    print("   • Press ENTER again to stop recording and send")
    print("   • Press ENTER during AI response to interrupt")
    print("   • Press Ctrl+C to exit")
    print("-" * 50)
    
    # Setup MCP connection
    async with MCPServerSse(
        name="ZeroEntropy",
        params={
            "url": MCP_URL,
            "headers": {
                "Authorization": f"Bearer {ZEROENTROPY_API_KEY}",
                "X-Collection-Name": COLLECTION_NAME,
            }
        },
        client_session_timeout_seconds=10.0,
    ) as search_server:
        
        # Create agent
        agent = Agent(
            name="ZeroEntropyVoiceAgent",
            instructions=SYSTEM_PROMPT,
            mcp_servers=[search_server],
            model="gpt-4.1-mini",
        )
        
        # Setup voice pipeline
        tts_settings = TTSModelSettings(instructions=TTS_PROMPT)
        voice_config = VoicePipelineConfig(tts_settings=tts_settings)
        workflow = SingleAgentVoiceWorkflow(agent)
        pipeline = VoicePipeline(workflow=workflow, config=voice_config)
        
        # Setup audio output
        output_stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16"
        )
        output_stream.start()
        
        try:
            while True:
                # Record user input
                audio_array = record_enter_to_talk()
                if audio_array is None:
                    continue
                
                # Process request
                user_input = AudioInput(buffer=audio_array)
                result = await pipeline.run(user_input)
                
                # Setup interruption detection
                stop_playback = threading.Event()
                interrupt_thread = None
                
                def monitor_interrupt():
                    """Monitor for Enter key press to interrupt response."""
                    try:
                        # Set a very short timeout for input() to make it non-blocking-ish
                        # We'll use a simple approach: try to read input with a timeout
                        import select
                        import sys
                        
                        while not stop_playback.is_set():
                            # Check if input is available (Unix/macOS only)
                            if hasattr(select, 'select'):
                                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                                if ready:
                                    # Consume the input line
                                    sys.stdin.readline()
                                    stop_playback.set()
                                    return
                            else:
                                # Fallback for Windows - less responsive
                                time.sleep(0.1)
                    except:
                        pass
                
                # Start interrupt monitoring thread
                interrupt_thread = threading.Thread(target=monitor_interrupt, daemon=True)
                interrupt_thread.start()
                
                # Stream response
                print("🤖 Assistant: ", end="", flush=True)
                try:
                    async for event in result.stream():
                        if stop_playback.is_set():
                            print("\n[Interrupted]")
                            break
                        if event.type == "voice_stream_event_audio":
                            output_stream.write(event.data)
                        elif event.type == "voice_stream_event_transcript":
                            print(event.text, end="", flush=True)
                except Exception:
                    pass
                
                # Signal the interrupt thread to stop
                stop_playback.set()
                
                print("\n" + "-" * 30)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        finally:
            output_stream.stop()
            output_stream.close()


async def main():
    """Main entry point."""
    if not ZEROENTROPY_API_KEY or not OPENAI_API_KEY:
        print("Error: Missing API keys. Set ZEROENTROPY_API_KEY and OPENAI_API_KEY")
        return
    
    # Setup data
    if not setup_yc_data():
        print("Failed to setup YC data")
        return
    
    # Run assistant
    await run_voice_assistant()


if __name__ == "__main__":
    asyncio.run(main())