# tts_app.py
import streamlit as st
from dotenv import load_dotenv
import os
from tts_engine import TTSEngine, VoicePresets
import time
import threading

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="TTS Engine", page_icon="🎤", layout="wide")

st.title("🎤 Text-to-Speech Engine")
st.markdown("Give your AI agent a natural voice")

# Initialize TTS engine
if 'tts' not in st.session_state:
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in .env file")
        st.stop()
    st.session_state.tts = TTSEngine(api_key)
    # Preload common phrases
    with st.spinner("Loading common phrases..."):
        st.session_state.tts.preload_common_phrases()

# Sidebar - Voice Controls
with st.sidebar:
    st.header("🎙️ Voice Settings")
    
    # Voice selection
    voice_options = st.session_state.tts.available_voices
    selected_voice = st.selectbox(
        "Voice",
        options=list(voice_options.keys()),
        format_func=lambda x: f"{x} - {voice_options[x]}",
        index=list(voice_options.keys()).index(st.session_state.tts.voice)
    )
    
    if selected_voice != st.session_state.tts.voice:
        st.session_state.tts.set_voice(selected_voice)
        st.success(f"Voice changed to {selected_voice}")
    
    # Speed control
    speed = st.slider(
        "Speaking Speed",
        min_value=0.5,
        max_value=2.0,
        value=st.session_state.tts.speed,
        step=0.05
    )
    if speed != st.session_state.tts.speed:
        st.session_state.tts.set_speed(speed)
    
    # Quality
    quality = st.selectbox(
        "Audio Quality",
        options=["standard", "hd"],
        index=0 if st.session_state.tts.model == "tts-1" else 1
    )
    st.session_state.tts.set_quality(quality)
    
    st.divider()
    
    # Voice Presets
    st.subheader("🎭 Quick Presets")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Friendly", use_container_width=True):
            preset = VoicePresets.friendly_assistant()
            st.session_state.tts.set_voice(preset["voice"])
            st.session_state.tts.set_speed(preset["speed"])
            st.rerun()
        if st.button("Professional", use_container_width=True):
            preset = VoicePresets.professional()
            st.session_state.tts.set_voice(preset["voice"])
            st.session_state.tts.set_speed(preset["speed"])
            st.rerun()
    with col2:
        if st.button("Empathetic", use_container_width=True):
            preset = VoicePresets.empathetic()
            st.session_state.tts.set_voice(preset["voice"])
            st.session_state.tts.set_speed(preset["speed"])
            st.rerun()
        if st.button("Quick", use_container_width=True):
            preset = VoicePresets.quick_response()
            st.session_state.tts.set_voice(preset["voice"])
            st.session_state.tts.set_speed(preset["speed"])
            st.rerun()
    
    st.divider()
    
    # Cache Management
    st.subheader("💾 Cache")
    stats = st.session_state.tts.get_cache_stats()
    st.metric("Cached Phrases", stats['total_cached'])
    st.metric("Cache Size", f"{stats['cache_size_mb']:.2f} MB")
    
    if st.button("🗑️ Clear Cache", type="secondary"):
        st.session_state.tts.clear_cache()
        st.success("Cache cleared!")
        st.rerun()
    
    if st.button("📦 Preload Common Phrases"):
        with st.spinner("Preloading..."):
            st.session_state.tts.preload_common_phrases()
        st.success("Preloading complete!")

# Main content - Two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Text Input")
    
    # Text input
    text_input = st.text_area(
        "Enter text to speak",
        height=150,
        placeholder="Type something for the agent to say...",
        value="Hello, this is CareCaller. I'm calling to check on your medication refill."
    )
    
    # Quick phrase buttons
    st.subheader("🔘 Quick Phrases")
    quick_phrases = [
        "Hello, this is CareCaller",
        "Have you experienced any side effects?",
        "Do you need a refill?",
        "Thank you for your time",
        "I understand, let me help you with that",
        "Please hold for a moment"
    ]
    
    cols = st.columns(3)
    for i, phrase in enumerate(quick_phrases):
        with cols[i % 3]:
            if st.button(phrase[:30], key=f"quick_{i}"):
                text_input = phrase
                st.session_state.speak_text = phrase
                st.rerun()
    
    # Speak button
    st.divider()
    
    if 'is_speaking' not in st.session_state:
        st.session_state.is_speaking = False
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔊 Speak", type="primary", use_container_width=True):
            if text_input.strip():
                st.session_state.is_speaking = True
                # Speak in background
                def speak_thread():
                    st.session_state.tts.speak(text_input, wait=True)
                    st.session_state.is_speaking = False
                threading.Thread(target=speak_thread, daemon=True).start()
                st.rerun()
    
    with col_btn2:
        if st.button("🛑 Stop", use_container_width=True):
            st.session_state.tts.stop_playback()
            st.session_state.is_speaking = False
            st.success("Stopped")
    
    with col_btn3:
        if st.button("⏸️ Test Cache", use_container_width=True):
            with st.spinner("Testing cache performance..."):
                test_phrase = "This is a test of the cache system"
                start = time.time()
                st.session_state.tts.speak(test_phrase, wait=True)
                first_time = time.time() - start
                
                start = time.time()
                st.session_state.tts.speak(test_phrase, wait=True)
                cache_time = time.time() - start
                
                st.success(f"First: {first_time:.2f}s | Cached: {cache_time:.2f}s | Speedup: {first_time/cache_time:.1f}x")
    
    # Status
    if st.session_state.is_speaking:
        st.warning("🔊 Currently speaking...")

with col2:
    st.header("🎚️ Advanced Settings")
    
    # Interruption handling
    st.subheader("⚡ Interruption")
    interrupt_mode = st.radio(
        "On new speech:",
        options=["Interrupt current", "Wait for completion"],
        index=0
    )
    
    # Voice preview
    st.subheader("🎤 Voice Preview")
    preview_text = st.text_input("Preview phrase", "Hello, how are you today?")
    if st.button("Preview Voice"):
        st.session_state.tts.speak(preview_text, wait=False)
    
    # Audio info
    st.divider()
    st.subheader("ℹ️ Audio Info")
    st.caption(f"**Model:** {st.session_state.tts.model.upper()}")
    st.caption(f"**Voice:** {st.session_state.tts.voice}")
    st.caption(f"**Speed:** {st.session_state.tts.speed}x")
    
    # Test different speeds
    st.subheader("🎵 Speed Test")
    test_text = "This is a speed test."
    for test_speed in [0.75, 1.0, 1.5]:
        if st.button(f"{test_speed}x Speed"):
            original_speed = st.session_state.tts.speed
            st.session_state.tts.set_speed(test_speed)
            st.session_state.tts.speak(test_text, wait=False)
            st.session_state.tts.set_speed(original_speed)

# Playback status
st.divider()
st.caption("💡 Tip: Common phrases are cached for instant playback after first use")
