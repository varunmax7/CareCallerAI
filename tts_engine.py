# tts_engine.py
from openai import OpenAI
import pygame
import io
import tempfile
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict
import time
import threading

class TTSEngine:
    def __init__(self, api_key: str, cache_dir: str = "tts_cache"):
        """Initialize Text-to-Speech engine"""
        self.client = OpenAI(api_key=api_key)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache for common phrases
        self.cache_index_path = self.cache_dir / "cache_index.json"
        self.cache_index = self.load_cache_index()
        
        # Audio playback
        try:
            pygame.mixer.init(frequency=24000)
            self.has_audio_hardware = True
        except Exception as e:
            print(f"⚠️ Audio hardware not detected (Headless Server): {e}")
            self.has_audio_hardware = False
        
        # Current playback state
        self.is_playing = False
        self.current_audio = None
        self.stop_requested = False
        
        # Voice settings
        self.voice = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
        self.speed = 1.0  # 0.25 to 4.0
        self.model = "tts-1"  # tts-1 or tts-1-hd
        
        # Available voices
        self.available_voices = {
            "alloy": "Neutral, professional",
            "echo": "Male, authoritative",
            "fable": "British, warm",
            "onyx": "Male, deep",
            "nova": "Female, friendly",
            "shimmer": "Female, empathetic"
        }
        
    def load_cache_index(self) -> Dict:
        """Load cache index from disk"""
        if self.cache_index_path.exists():
            with open(self.cache_index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache_index(self):
        """Save cache index to disk"""
        with open(self.cache_index_path, 'w') as f:
            json.dump(self.cache_index, f, indent=2)
    
    def get_cache_key(self, text: str) -> str:
        """Generate unique cache key for text"""
        # Normalize text for caching (lowercase, strip)
        normalized = text.lower().strip()
        return hashlib.md5(f"{normalized}_{self.voice}_{self.speed}_{self.model}".encode()).hexdigest()
    
    def is_common_phrase(self, text: str) -> bool:
        """Check if text is a common phrase that should be cached"""
        common_phrases = [
            "hello", "thank you", "goodbye", "yes", "no",
            "please", "sorry", "okay", "great", "welcome",
            "let me check", "one moment", "i understand"
        ]
        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in common_phrases)
    
    def cache_phrase(self, text: str, audio_data: bytes):
        """Cache audio data for a phrase"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        
        # Save audio file
        with open(cache_file, 'wb') as f:
            f.write(audio_data)
        
        # Update cache index
        self.cache_index[cache_key] = {
            "text": text,
            "voice": self.voice,
            "speed": self.speed,
            "model": self.model,
            "created": time.time(),
            "file": str(cache_file)
        }
        self.save_cache_index()
    
    def get_cached_audio(self, text: str) -> Optional[bytes]:
        """Get cached audio if available"""
        cache_key = self.get_cache_key(text)
        if cache_key in self.cache_index:
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return f.read()
        return None
    
    def text_to_speech(self, text: str, force_regenerate: bool = False) -> Optional[bytes]:
        """Convert text to speech using OpenAI TTS"""
        if not text or not text.strip():
            return None
        
        # Check cache first
        if not force_regenerate:
            cached = self.get_cached_audio(text)
            if cached:
                print(f"🎯 Using cached audio for: {text[:50]}...")
                return cached
        
        try:
            print(f"🎤 Generating TTS: {text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                speed=self.speed
            )
            
            # Get audio data
            audio_data = response.content
            
            # Cache if common phrase
            if self.is_common_phrase(text):
                self.cache_phrase(text, audio_data)
            
            return audio_data
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return None
    
    def play_audio(self, audio_data: bytes, interrupt: bool = True):
        """Play audio through speakers"""
        if not audio_data:
            return
        
        # Stop current playback if interrupt requested
        if interrupt and self.is_playing:
            self.stop_playback()
            time.sleep(0.1)  # Allow cleanup
        
        # Create temporary file for pygame
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            # Load and play
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.stop_requested = False
            
            # Wait for playback to finish or be stopped
            while pygame.mixer.music.get_busy() and not self.stop_requested:
                pygame.time.wait(100)
            
            self.is_playing = False
            
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def play_async(self, audio_data: bytes, interrupt: bool = True):
        """Play audio in background thread"""
        thread = threading.Thread(target=self.play_audio, args=(audio_data, interrupt))
        thread.daemon = True
        thread.start()
        return thread
    
    def stop_playback(self):
        """Stop current playback"""
        self.stop_requested = True
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def speak(self, text: str, voice: str = None, speed: float = None, wait: bool = True, interrupt: bool = True):
        """Main method to speak text"""
        if voice:
            self.set_voice(voice)
        if speed:
            self.set_speed(speed)
            
        audio_data = self.text_to_speech(text)
        if audio_data:
            if wait:
                self.play_audio(audio_data, interrupt)
            else:
                self.play_async(audio_data, interrupt)
            return True
        return False
    
    def set_voice(self, voice: str):
        """Change voice"""
        if voice in self.available_voices:
            self.voice = voice
            return True
        return False
    
    def set_speed(self, speed: float):
        """Change speaking speed (0.25 to 4.0)"""
        self.speed = max(0.25, min(4.0, speed))
        return self.speed
    
    def set_quality(self, quality: str):
        """Set audio quality (standard or hd)"""
        if quality == "hd":
            self.model = "tts-1-hd"
        else:
            self.model = "tts-1"
    
    def preload_common_phrases(self):
        """Pre-cache common phrases for faster response"""
        common_phrases = [
            "Hello, this is CareCaller",
            "Thank you for your time",
            "Have a great day",
            "I understand",
            "Please hold for a moment",
            "Let me check that for you",
            "I'm sorry, I didn't catch that",
            "Could you please repeat that?",
            "Great, thank you",
            "One moment please"
        ]
        
        print("📦 Preloading common phrases...")
        for phrase in common_phrases:
            if not self.get_cached_audio(phrase):
                self.text_to_speech(phrase)
        print("✅ Preloading complete")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_cached": len(self.cache_index),
            "cache_size_mb": sum(
                (self.cache_dir / f"{key}.mp3").stat().st_size 
                for key in self.cache_index.keys() 
                if (self.cache_dir / f"{key}.mp3").exists()
            ) / (1024 * 1024),
            "voices": set(item["voice"] for item in self.cache_index.values())
        }
    
    def clear_cache(self):
        """Clear all cached audio"""
        for key in self.cache_index:
            cache_file = self.cache_dir / f"{key}.mp3"
            if cache_file.exists():
                cache_file.unlink()
        self.cache_index = {}
        self.save_cache_index()
        print("🗑️ Cache cleared")

# Voice presets for different scenarios
class VoicePresets:
    SHIMMER = "shimmer"
    ALLOY = "alloy"
    NOVA = "nova"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"

    @staticmethod
    def friendly_assistant():
        return {"voice": "nova", "speed": 1.0, "model": "tts-1"}
    
    @staticmethod
    def professional():
        return {"voice": "alloy", "speed": 0.9, "model": "tts-1-hd"}
    
    @staticmethod
    def empathetic():
        return {"voice": "shimmer", "speed": 0.85, "model": "tts-1-hd"}
    
    @staticmethod
    def quick_response():
        return {"voice": "onyx", "speed": 1.2, "model": "tts-1"}
