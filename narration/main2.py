import os
import asyncio
import base64
import io
import time
import subprocess
import tempfile
import sys
from PIL import ImageGrab, Image
from io import BytesIO
import aiohttp
from openai import AsyncOpenAI

# Set your API keys
ELEVENLABS_API_KEY = "sk_912a9fff1d5557139bc8b8977d56083397b97571570a15af"
OPENAI_API_KEY = "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"

# Voice settings
VOICE_NAME = "Deep Lax"
VOICE_ID = "qZkuFcRFTdS6vkYu5ABx"  # Using the requested Deep Lax voice ID

# Initialize clients
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Global variables
is_running = True
narration_history = []
last_image_data = None

# Configure platform
PLATFORM = 'unknown'
if sys.platform.startswith('darwin'):
    PLATFORM = 'mac'
elif sys.platform.startswith('win'):
    PLATFORM = 'windows'
elif sys.platform.startswith('linux'):
    PLATFORM = 'linux'

def play_audio_file(file_path):
    """Play audio file using platform-specific commands"""
    print(f"DEBUG: Playing audio from {file_path}")
    try:
        if PLATFORM == 'mac':
            subprocess.run(['afplay', file_path], check=True)
            print("DEBUG: afplay completed")
        elif PLATFORM == 'windows':
            subprocess.run(['start', file_path], shell=True, check=True)
            print("DEBUG: Windows player completed")
        elif PLATFORM == 'linux':
            subprocess.run(['aplay', file_path], check=True)
            print("DEBUG: Linux player completed")
        else:
            print(f"DEBUG: Unsupported platform: {PLATFORM}")
    except subprocess.SubprocessError as e:
        print(f"ERROR: Audio playback failed: {e}")

def capture_screen():
    """Basic screen capture"""
    try:
        print("DEBUG: Capturing screen")
        screenshot = ImageGrab.grab()
        
        # Resize to reduce processing time
        screenshot.thumbnail((800, 600))
        
        # Convert RGBA to RGB if needed
        if screenshot.mode == 'RGBA':
            screenshot = screenshot.convert('RGB')
            
        print(f"DEBUG: Screenshot captured: {screenshot.size}")
        return screenshot
    except Exception as e:
        print(f"ERROR: Screen capture failed: {e}")
        return None

def encode_image(image):
    """Convert image to base64 string"""
    try:
        image_io = BytesIO()
        image.save(image_io, format="JPEG", quality=70)
        image_io.seek(0)
        image_bytes = image_io.read()
        base64_image = base64.b64encode(image_bytes).decode()
        print(f"DEBUG: Image encoded: {len(base64_image)} bytes")
        return base64_image
    except Exception as e:
        print(f"ERROR: Image encoding failed: {e}")
        return None

async def analyze_screen(base64_image):
    """Analyze screen content with Vision API"""
    print("DEBUG: Analyzing screen with Vision API")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a  funny game narrator. Describe the main action in 2-3 sentences"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's happening in this game screen, decribe in detail and predict next action?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=50
        )
        
        narration = response.choices[0].message.content
        print(f"DEBUG: Got narration: {narration}")
        return narration
    except Exception as e:
        print(f"ERROR: Vision API call failed: {e}")
        return None

async def text_to_speech(text):
    """Convert text to speech using ElevenLabs API with Deep Lax voice"""
    print(f"DEBUG: Converting to speech with {VOICE_NAME}: {text}")
    try:
        # Using Deep Lax voice ID
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        print(f"DEBUG: Sending request to ElevenLabs with {VOICE_NAME} voice")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"DEBUG: ElevenLabs response status: {response.status}")
                if response.status == 200:
                    audio_bytes = await response.read()
                    print(f"DEBUG: Got audio response: {len(audio_bytes)} bytes")
                    
                    # Save to temp file
                    temp_path = tempfile.gettempdir() + "/debug_narration.mp3"
                    with open(temp_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    print(f"DEBUG: Saved audio to {temp_path}")
                    return temp_path
                else:
                    error_text = await response.text()
                    print(f"ERROR: TTS API error: {response.status}")
                    print(f"ERROR: {error_text[:200]}")
                    return None
    except Exception as e:
        print(f"ERROR: Text-to-speech conversion failed: {e}")
        return None

async def process_screen():
    """Process a single screen capture"""
    global last_image_data, narration_history
    
    try:
        # Capture screen
        image = capture_screen()
        if not image:
            print("DEBUG: No image captured")
            return
            
        # Encode image
        base64_image = encode_image(image)
        if not base64_image:
            print("DEBUG: Image encoding failed")
            return
            
        # Skip if same as last image
        if base64_image == last_image_data:
            print("DEBUG: Screen unchanged, skipping")
            return
            
        # Update last image
        last_image_data = base64_image
        
        # Analyze image
        narration = await analyze_screen(base64_image)
        if not narration:
            print("DEBUG: No narration generated")
            return
            
        # Save to history
        narration_history.append(narration)
        if len(narration_history) > 5:
            narration_history.pop(0)
            
        # Convert to speech
        audio_path = await text_to_speech(narration)
        if not audio_path:
            print("DEBUG: No audio file generated")
            return
            
        # Play audio
        play_audio_file(audio_path)
        
        return narration
    except Exception as e:
        print(f"ERROR: Screen processing failed: {e}")
        return None

async def main():
    """Main function with simplified flow and better debugging"""
    global is_running
    
    print("DEBUG: Starting simplified game narration")
    print(f"Using voice: {VOICE_NAME}")
    print("Press Ctrl+C to stop at any time")
    
    narration_count = 0
    
    try:
        while is_running:
            print("\nDEBUG: Starting new capture cycle")
            
            # Process screen
            narration = await process_screen()
            
            if narration:
                narration_count += 1
                print(f"\nNarration {narration_count}: {narration}")
            
            # Wait before next capture
            print("DEBUG: Waiting before next capture")
            await asyncio.sleep(3.0)
            
    except KeyboardInterrupt:
        print("\nDEBUG: Keyboard interrupt detected")
        is_running = False
    except Exception as e:
        print(f"ERROR: Main loop exception: {e}")
    finally:
        print("DEBUG: Cleaning up")
        try:
            temp_path = tempfile.gettempdir() + "/debug_narration.mp3"
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"ERROR: Cleanup failed: {e}")
            
    print("DEBUG: Application closed")

if __name__ == "__main__":
    try:
        print("DEBUG: Starting application")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDEBUG: Exiting from main")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Application failure: {e}")