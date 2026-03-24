# integrated_agent.py
import streamlit as st
import os
from dotenv import load_dotenv
from agent_core import VoiceAgent
from tts_engine import TTSEngine

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Complete Voice Agent", page_icon="🤖", layout="wide")

st.title("🤖🎤 Complete Voice Agent")
st.markdown("Speech-to-Text + Agent Intelligence + Text-to-Speech")

# Initialize components
if 'agent' not in st.session_state:
    st.session_state.agent = VoiceAgent(api_key)
    st.session_state.tts = TTSEngine(api_key)
    st.session_state.messages = []
    st.session_state.auto_speak = True

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.auto_speak = st.checkbox("Auto-speak responses", value=True)
    
    if st.session_state.auto_speak:
        st.subheader("Voice Settings")
        voice = st.selectbox(
            "Voice",
            options=list(st.session_state.tts.available_voices.keys()),
            index=0
        )
        st.session_state.tts.set_voice(voice)
        
        speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.05)
        st.session_state.tts.set_speed(speed)
    
    if st.button("🔄 Reset Call"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()

# Chat interface
st.header("💬 Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            if st.session_state.auto_speak and msg.get("speak", True):
                # Auto-speak agent messages
                st.session_state.tts.speak(msg["content"], wait=False, interrupt=True)

# Input methods
input_method = st.radio("Input method:", ["Text", "Voice (Coming Soon)"], horizontal=True)

if input_method == "Text":
    user_input = st.chat_input("Type your response...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Process with agent
        response = st.session_state.agent.process_user_input(user_input)
        
        # Add agent response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response['agent_message'],
            "speak": True
        })
        
        st.rerun()

# Show call progress
with st.expander("📊 Call Progress"):
    completion = st.session_state.agent.get_completion_status()
    st.progress(completion['completion_rate'])
    st.write(f"Questions: {completion['answered']}/{completion['total_questions']}")
    
    if st.session_state.agent.responses_json:
        st.json(st.session_state.agent.responses_json)
