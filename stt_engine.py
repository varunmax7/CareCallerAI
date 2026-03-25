# stt_engine.py
from openai import OpenAI
try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import soundfile as sf
except ImportError:
    sf = None

import numpy as np
import tempfile
import os
from pathlib import Path
import time

class STTEngine:
    def __init__(self, api_key):
        """Initialize the Speech-to-Text engine with OpenAI API"""
        self.client = OpenAI(api_key=api_key)
        self.sample_rate = 16000  # Whisper works best at 16kHz
        self.is_recording = False
        self.audio_data = []
        
        # Check for sound hardware and library availability
        if sd is None:
            print("⚠️ sounddevice library not installed. STT disabled.")
            self.has_hardware = False
            return

        try:
            sd.query_devices()
            self.has_hardware = True
        except Exception as e:
            print(f"⚠️ No sound hardware detected for STT: {e}")
            self.has_hardware = False
        
    def start_recording(self):
        """Start recording from microphone"""
        self.is_recording = True
        self.audio_data = []
        print("🎤 Recording... Speak now!")
        
        # Define callback to collect audio chunks
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        if sd is None or not self.has_hardware:
            print("❌ Cannot start recording: No audio hardware/library")
            return

        # Start recording stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=callback,
            dtype=np.float32
        )
        self.stream.start()
        
    def stop_recording(self):
        """Stop recording and transcribe the audio"""
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if not self.audio_data:
            return None
            
        # Combine all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        if sf:
            sf.write(temp_file.name, audio_array, self.sample_rate)
        else:
            print("❌ Cannot save audio: soundfile library not available")
            return None
        
        # Transcribe using Whisper API
        print("📝 Transcribing...")
        try:
            with open(temp_file.name, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return response.text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def record_and_transcribe(self, duration=None):
        """Simple one-shot recording and transcription"""
        print("🎤 Recording... Speak now!")
        
        if sd is None or not self.has_hardware:
            print("❌ Cannot record: No audio hardware/library")
            return None

        if duration:
            # Record for fixed duration
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
        else:
            # Record until Enter
            self.start_recording()
            input("Press Enter when done speaking...")
            self.is_recording = False
            self.stream.stop()
            self.stream.close()
            audio = np.concatenate(self.audio_data, axis=0)
        
        # Save and transcribe
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        sf.write(temp_file.name, audio, self.sample_rate)
        
        print("📝 Transcribing...")
        try:
            with open(temp_file.name, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            os.unlink(temp_file.name)
            return response.text
        except Exception as e:
            print(f"Transcription Error: {e}")
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return None
    def record_audio(self, duration=5):
        """Record audio and return the path to the temporary file"""
        if sd is None or not self.has_hardware:
            print("❌ Cannot record: No audio hardware/library")
            return None

        print(f"🎤 Recording for {duration} seconds...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        if sf:
            sf.write(temp_file.name, audio, self.sample_rate)
        return temp_file.name

    def transcribe(self, audio_file_path):
        """Transcribe an audio file and return the text"""
        print(f"📝 Transcribing {audio_file_path}...")
        try:
            with open(audio_file_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            # Clean up temp file if it's in temp directory
            if "/tmp" in audio_file_path or "var/folders" in audio_file_path:
                try:
                    os.unlink(audio_file_path)
                except:
                    pass
            
            return response.text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
