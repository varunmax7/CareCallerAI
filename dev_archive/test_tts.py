# test_tts.py
import os
from dotenv import load_dotenv
from tts_engine import TTSEngine
import time

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ Please set OPENAI_API_KEY in .env file")
    exit(1)

# Create TTS engine
tts = TTSEngine(api_key)

print("\n" + "="*60)
print("🎤 Text-to-Speech Test")
print("="*60)

# Test different voices
test_phrases = [
    "Hello, this is CareCaller calling for your medication refill check-in.",
    "Have you experienced any side effects from your medication?",
    "I understand you'd like to reschedule. When would be a better time?",
    "Thank you for your time. Have a great day!"
]

# Test each voice
for voice_name, voice_desc in tts.available_voices.items():
    print(f"\n📢 Testing voice: {voice_name} ({voice_desc})")
    tts.set_voice(voice_name)
    
    for phrase in test_phrases[:1]:  # Test first phrase only
        print(f"  Speaking: {phrase[:50]}...")
        tts.speak(phrase, wait=True)
        time.sleep(0.5)

# Test speed variations
print("\n\n⚡ Testing Speed Variations")
tts.set_voice("nova")

for speed in [0.75, 1.0, 1.5]:
    print(f"\n  Speed: {speed}x")
    tts.set_speed(speed)
    tts.speak("This is a test of speaking speed.", wait=True)
    time.sleep(0.5)

# Test caching
print("\n\n💾 Testing Cache")
tts.set_speed(1.0)
test_phrase = "Thank you for calling CareCaller."

print("  First call (should generate)...")
start = time.time()
tts.speak(test_phrase, wait=True)
gen_time = time.time() - start

print("  Second call (should use cache)...")
start = time.time()
tts.speak(test_phrase, wait=True)
cache_time = time.time() - start

print(f"\n  Generation time: {gen_time:.2f}s")
print(f"  Cache time: {cache_time:.2f}s")
print(f"  Speedup: {gen_time/cache_time:.1f}x")

# Show cache stats
stats = tts.get_cache_stats()
print(f"\n📊 Cache Stats:")
print(f"  Total cached: {stats['total_cached']}")
print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")

print("\n✅ TTS test complete!")
