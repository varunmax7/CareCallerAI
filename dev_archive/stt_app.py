# stt_app.py
import streamlit as st
import openai
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os
from dotenv import load_dotenv
import time

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="CareCaller STT", page_icon="🎤")

st.title("🎤 Speech-to-Text Engine")
st.markdown("Convert speech to text using OpenAI Whisper")

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = []

# Recording parameters
SAMPLE_RATE = 16000
DURATION = 5  # seconds for demo

# Custom CSS for buttons
st.markdown("""
<style>
.big-button {
    font-size: 20px;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎙️ Record (5 sec)", type="primary", use_container_width=True):
        st.session_state.transcript = ""
        st.session_state.audio_data = []
        
        with st.status("Recording...", expanded=True) as status:
            st.write("🎤 Listening for 5 seconds...")
            
            # Record audio
            audio = sd.rec(
                int(DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            st.write("📝 Transcribing with Whisper...")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                sf.write(tmp_file.name, audio, SAMPLE_RATE)
                
                # Transcribe
                with open(tmp_file.name, 'rb') as audio_file:
                    response = openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                os.unlink(tmp_file.name)
            
            st.session_state.transcript = response.text
            status.update(label="Done!", state="complete")
        
        st.rerun()

with col2:
    if st.button("⏹️ Record (Manual)", use_container_width=True):
        st.session_state.transcript = ""
        
        st.info("🎤 Recording... Press 'Stop Recording' when done")
        st.session_state.recording = True
        
        # Start recording
        def callback(indata, frames, time, status):
            if st.session_state.recording:
                st.session_state.audio_data.append(indata.copy())
        
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=callback,
            dtype=np.float32
        )
        stream.start()
        
        # Store stream in session state
        st.session_state.stream = stream

with col3:
    if st.button("🛑 Stop Recording", use_container_width=True):
        if 'stream' in st.session_state:
            st.session_state.stream.stop()
            st.session_state.stream.close()
            st.session_state.recording = False
            
            # Process recorded audio
            if st.session_state.audio_data:
                audio_array = np.concatenate(st.session_state.audio_data, axis=0)
                
                with st.status("Transcribing...", expanded=True):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        sf.write(tmp_file.name, audio_array, SAMPLE_RATE)
                        
                        with open(tmp_file.name, 'rb') as audio_file:
                            response = openai.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file
                            )
                        
                        os.unlink(tmp_file.name)
                    
                    st.session_state.transcript = response.text
                
                st.session_state.audio_data = []
                st.rerun()

# Display transcript
st.divider()
st.subheader("📝 Transcription Result")

if st.session_state.transcript:
    st.success(st.session_state.transcript)
    
    # Add copy button
    if st.button("📋 Copy to Clipboard"):
        st.write("Copied!")
        st.session_state.copy_text = st.session_state.transcript
else:
    st.info("Click a record button above and speak into your microphone")

# Add a text input for manual testing
st.divider()
st.subheader("✏️ Manual Test")
manual_text = st.text_area("Or type text to test the flow:")
if manual_text:
    st.session_state.transcript = manual_text
    st.success("Text saved as transcript!")

# Show status
st.divider()
st.caption(f"API Status: {'✅ Connected' if openai.api_key else '❌ No API Key'}")
