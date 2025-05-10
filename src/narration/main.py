import os
import sounddevice as sd
import numpy as np
import wave
import asyncio
import aiohttp
import io
import json
import threading
import queue
import time
from openai import AsyncOpenAI
from elevenlabs import generate, play, set_api_key
from elevenlabs import voice as elevenlabs_voice

# Set your API keys
ELEVENLABS_API_KEY = ""
OPENAI_API_KEY = ""

# Initialize clients
client = AsyncOpenAI(api_key=OPENAI_API_KEY)
set_api_key(ELEVENLABS_API_KEY)

# Global variables for conversation state
is_ai_speaking = False
speech_interrupted = False
tts_cache = {}
response_cache = {}
audio_queue = queue.Queue()
playback_thread = None
playback_event = threading.Event()

def normalize_audio(audio_data):
    """Normalize audio volume"""
    max_value = np.max(np.abs(audio_data))
    if max_value > 0:
        return audio_data / max_value
    return audio_data

def is_speech_detected(indata, threshold=0.02):
    """Detect if speech is present in audio data"""
    return np.max(np.abs(indata)) > threshold

def monitor_for_interruption(stream, duration=0.5):
    """Monitor microphone input for potential interruption"""
    global speech_interrupted
    
    # Check if significant audio is detected
    data = stream.read(int(sd.default.samplerate * duration))[0]
    if is_speech_detected(data):
        speech_interrupted = True
        return True
    return False

def playback_worker():
    """Background thread for audio playback with interruption detection"""
    global is_ai_speaking, speech_interrupted
    
    # Set up microphone monitoring
    sd.default.channels = 1
    sd.default.samplerate = 44100
    
    while True:
        try:
            # Wait for an audio item in the queue
            audio_data = audio_queue.get()
            if audio_data is None:  # Signal to exit
                break
                
            # Indicate AI is speaking
            is_ai_speaking = True
            speech_interrupted = False
            
            # Start the playback
            with sd.InputStream() as stream:
                play(audio_data)
                
                # Check for interruption during playback
                # This is simplified - a real implementation would need more robust detection
                # while is_ai_speaking and not speech_interrupted:
                #     if monitor_for_interruption(stream):
                #         print("\n[User interrupted]")
                #         break
                #     time.sleep(0.2)
            
            # Reset speaking state
            is_ai_speaking = False
            audio_queue.task_done()
            
        except Exception as e:
            print(f"Playback error: {e}")
            is_ai_speaking = False
    
    print("Playback thread exiting")

async def record_audio_with_vad(max_duration=5, sample_rate=44100, silence_threshold=0.01, silence_timeout=1.0):
    """Record audio with voice activity detection to stop when silence is detected"""
    global is_ai_speaking, speech_interrupted
    
    # If AI is speaking, mark as interrupted
    if is_ai_speaking:
        speech_interrupted = True
        print("\n[Listening for new input...]")
    else:
        print("Recording... Speak now!")
    
    # Configure sounddevice
    sd.default.channels = 1
    sd.default.samplerate = sample_rate
    
    # Create a buffer to store audio data
    audio_buffer = []
    is_speaking = False
    silence_duration = 0
    total_duration = 0
    
    # Create an event to signal when to stop recording
    stop_event = asyncio.Event()
    
    def callback(indata, frames, time, status):
        nonlocal is_speaking, silence_duration, total_duration
        
        # Add audio data to buffer
        audio_buffer.append(indata.copy())
        
        # Update total duration
        chunk_duration = frames / sample_rate
        total_duration += chunk_duration
        
        # Check if current chunk contains speech
        current_volume = np.max(np.abs(indata))
        
        if current_volume > silence_threshold:
            is_speaking = True
            silence_duration = 0
        elif is_speaking:
            # Count silence after speech
            silence_duration += chunk_duration
            if silence_duration >= silence_timeout:
                # Enough silence, stop recording
                stop_event.set()
        
        # Also stop if we reach maximum duration
        if total_duration >= max_duration:
            stop_event.set()
    
    # Start recording with callback
    stream = sd.InputStream(callback=callback, channels=1, samplerate=sample_rate)
    with stream:
        # Wait until stop_event is set or max_duration is reached
        try:
            # Give a small delay to allow speech to be detected
            await asyncio.sleep(0.5)
            
            # Wait for stop event or timeout
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=max_duration)
            except asyncio.TimeoutError:
                pass
        except KeyboardInterrupt:
            pass
    
    print("Recording finished!")
    
    # Combine all audio chunks
    if not audio_buffer:
        return np.array([])
    
    recording = np.concatenate(audio_buffer)
    # Normalize the audio
    recording = normalize_audio(recording)
    return recording

async def speech_to_text_inmemory(audio_data, sample_rate=44100):
    """Convert speech to text using in-memory audio data"""
    try:
        print("Converting speech to text...")
        
        # Convert numpy array to WAV format in memory
        audio_bytes = io.BytesIO()
        with wave.open(audio_bytes, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Convert to 16-bit PCM
            audio_int = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int.tobytes())
        
        # Reset the buffer position for reading
        audio_bytes.seek(0)
        
        # Use aiohttp for async request
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', 
                          audio_bytes, 
                          filename='audio.wav',
                          content_type='audio/wav')
            data.add_field('model_id', 'scribe_v1')
            
            headers = {"xi-api-key": ELEVENLABS_API_KEY}
            
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("text", "")
                else:
                    error_text = await response.text()
                    print(f"Error: API returned status code {response.status}")
                    print(f"Response: {error_text}")
                    return None
                
    except Exception as e:
        print(f"Error during speech-to-text conversion: {str(e)}")
        return None

async def get_chat_response(text, conversation_history=None):
    """Get response from OpenAI API with conversation history"""
    try:
        # If no history provided, initialize it
        if conversation_history is None:
            conversation_history = [{"role": "system", "content": "You are a helpful assistant. Keep responses concise."}]
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": text})
        
        # Check cache with the conversation state
        cache_key = str(conversation_history)
        if cache_key in response_cache:
            print("Using cached response")
            return response_cache[cache_key], conversation_history
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )
        
        result = response.choices[0].message.content
        
        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": result})
        
        # Cache the response
        response_cache[cache_key] = result
        return result, conversation_history
    except Exception as e:
        print(f"Error getting chat response: {e}")
        return None, conversation_history

async def text_to_speech_full(text):
    """Convert text to speech using ElevenLabs with fast turbo model"""
    global audio_queue
    
    try:
        if not text or text.isspace():
            return
            
        print(f"Converting response to speech...")
        
        # Check TTS cache
        if text in tts_cache:
            print("Using cached TTS audio")
            audio_data = tts_cache[text]
        else:
            # Generate audio with faster model
            audio_data = generate(
                text=text,
                voice="Josh",
                model="eleven_turbo_v2"  # Faster model for quicker generation
            )
            # Cache the audio
            tts_cache[text] = audio_data
        
        # Add to playback queue
        audio_queue.put(audio_data)
        
    except Exception as e:
        print(f"Error in text-to-speech conversion: {e}")

async def main_async():
    global playback_thread, audio_queue, is_ai_speaking, speech_interrupted
    
    print("Welcome to Enhanced Voice Chat! Press Ctrl+C to exit.")
    print("Speak naturally - you can interrupt the AI response by speaking.")
    
    # Start the playback thread
    playback_thread = threading.Thread(target=playback_worker, daemon=True)
    playback_thread.start()
    
    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": "You are a helpful assistant. Keep responses concise and natural."}
    ]
    
    while True:
        try:
            # Record audio with voice activity detection
            recording = await record_audio_with_vad(max_duration=10)
            
            if len(recording) > 0:
                # Process speech to text asynchronously
                text = await speech_to_text_inmemory(recording)
                
                if text and text.strip():
                    print(f"\nYou said: {text}")
                    
                    # Get response with conversation history
                    response, conversation_history = await get_chat_response(text, conversation_history)
                    
                    if response:
                        print(f"\nAI: {response}")
                        
                        # Convert full response to speech
                        await text_to_speech_full(response)
                        
                        print("\nReady for next input! (You can speak to interrupt)")
                    else:
                        print("Failed to get AI response. Please try again.")
                else:
                    print("No speech detected or could not transcribe. Please try again.")
            else:
                print("No audio recorded. Please try again.")
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            # Signal playback thread to exit
            audio_queue.put(None)
            playback_thread.join(timeout=1.0)
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Trying again...")

def main():
    # Run the async main function
    asyncio.run(main_async())

if __name__ == "__main__":
    main()