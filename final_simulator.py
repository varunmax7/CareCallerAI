# final_simulator.py
import streamlit as st
import os
from dotenv import load_dotenv
import time
import json
import base64
from datetime import datetime
from pathlib import Path

# Import our engines
from stt_engine import STTEngine
from agent_core import VoiceAgent
from tts_engine import TTSEngine, VoicePresets
from fpdf import FPDF
import pandas as pd

# PDF Report Generator
def generate_pdf_report(data):
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    page_width = 180 # Safe width for A4 with 15mm margins
    
    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(13, 110, 253) # Blue
    pdf.cell(page_width, 20, "CareCaller Call Report", ln=True, align="C")
    
    # Header Info
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(page_width, 10, f"Call ID: {data['call_id']}", ln=True)
    pdf.cell(page_width, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(page_width, 10, f"Outcome: {data['outcome'].replace('_', ' ').title()}", ln=True)
    pdf.ln(5)
    
    # Patient Data
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(page_width, 10, "Patient Profile Summary", ln=True)
    pdf.set_font("Helvetica", "", 12)
    profile = data.get('patient_profile', {})
    if profile:
        pdf.cell(page_width, 8, f"Name: {profile.get('name', 'N/A')}", ln=True)
        pdf.cell(page_width, 8, f"Confirmed Identity: {'Yes' if profile.get('confirmed') else 'No'}", ln=True)
        
        meds = profile.get('medications', [])
        med_str = ", ".join([m['name'] for m in meds]) if meds else "None"
        pdf.multi_cell(page_width, 8, f"Current Medications: {med_str}", ln=True)
        
        allergies = profile.get('allergies', [])
        all_str = ", ".join(allergies) if allergies else "None reported"
        pdf.cell(page_width, 8, f"Allergies: {all_str}", ln=True)
    
    pdf.ln(10)
    
    # Extracted Data
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(page_width, 10, "Extracted Health Data", ln=True)
    pdf.set_font("Helvetica", "", 11)
    
    responses = data.get('responses_json', [])
    for resp in responses:
        if resp.get('answer'):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(page_width, 8, f"Q: {resp['question']}", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(page_width, 8, f"A: {resp['answer']} (Confidence: {resp.get('confidence', 0):.0%})", ln=True)
            pdf.ln(2)
            
    pdf.ln(10)
    
    # Transcript
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(page_width, 10, "Full Call Transcript", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(page_width, 5, data['transcript_text'], ln=True)
    
    return pdf.output()

# Load configuration
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="CareCaller AI Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium look
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .agent-bubble {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 15px 15px 15px 0px;
        margin-bottom: 10px;
        border-left: 5px solid #0d6efd;
        color: #111;
        font-size: 1.1rem;
    }
    .patient-bubble {
        background-color: #d1e7dd;
        padding: 15px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 10px;
        text-align: right;
        border-right: 5px solid #198754;
        color: #111;
        font-size: 1.1rem;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-active { background-color: #d1e7dd; color: #0f5132; }
    .status-ended { background-color: #f8d7da; color: #842029; }
</style>
""", unsafe_allow_html=True)

# Initialize engines (re-cached to pick up agent changes)
@st.cache_resource
def get_voice_engines(api_key, v):
    if not api_key or api_key == "sk-your-actual-key-here":
        return None, None, None
    stt = STTEngine(api_key)
    agent = VoiceAgent(api_key)
    tts = TTSEngine(api_key)
    return stt, agent, tts

stt, agent, tts = get_voice_engines(api_key, "1.0.1")

# Session state initialization
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'call_active' not in st.session_state:
    st.session_state.call_active = False
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'last_transcription' not in st.session_state:
    st.session_state.last_transcription = ""

# Sidebar - Settings & Stats
with st.sidebar:
    st.title("🎙️ CareCaller AI")
    st.caption("v1.0.1 - Full Simulator")
    
    if st.button("🧹 Force Reset System", use_container_width=True):
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    if not api_key or api_key == "sk-your-actual-key-here":
        st.error("Please set your OPENAI_API_KEY in the .env file")
        st.stop()
    
    # Voice Settings
    st.header("🔊 Voice Settings")
    voice_option = st.selectbox(
        "Agent Voice",
        options=["Shimmer (Female, Friendly)", "Alloy (Neutral)", "Nova (Female, Professional)", "Echo (Male)"],
        index=0
    )
    voice_map = {
        "Shimmer (Female, Friendly)": VoicePresets.SHIMMER,
        "Alloy (Neutral)": VoicePresets.ALLOY,
        "Nova (Female, Professional)": VoicePresets.NOVA,
        "Echo (Male)": VoicePresets.ECHO
    }
    
    speed = st.slider("Speaking Speed", 0.5, 1.5, 1.0, 0.1)
    
    st.divider()
    
    # Progress
    if st.session_state.call_active:
        st.header("📊 Call Progress")
        progress = agent.question_controller.get_progress()
        st.progress(progress['completion_rate'])
        st.caption(f"Questions: {progress['answered']}/{progress['total_questions']}")
        
        # Topic status
        st.subheader("📁 Topics Covered")
        status = agent.context_memory.get_topic_status()
        covered = [t for t, s in status.items() if s['covered']]
        for topic in covered:
            st.write(f"✅ {topic.replace('_', ' ').title()}")
            
    st.divider()
    
    # Patient Settings
    st.header("👤 Patient Data")
    sim_patient_name = st.text_input("Patient Name", value="Mr. Johnson")
    
    if st.button("🔄 Reset Call", type="secondary", use_container_width=True):
        agent.reset(sim_patient_name)
        st.session_state.conversation = []
        st.session_state.call_active = False
        st.rerun()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📞 Active Call Simulator")
    status_class = "status-active" if st.session_state.call_active else "status-ended"
    status_text = "CALL IN PROGRESS" if st.session_state.call_active else "CALL DISCONNECTED"
    st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)

with col2:
    if not st.session_state.call_active:
        if st.button("📞 Start Call", type="primary", use_container_width=True):
            st.session_state.call_active = True
            # Get initial greeting from agent
            agent.reset(sim_patient_name)
            response = agent.process_user_input("")
            greeting = response["agent_message"]
            st.session_state.conversation = [{"role": "agent", "content": greeting}]
            if getattr(tts, 'has_audio_hardware', False):
                tts.speak(greeting, voice=voice_map[voice_option], speed=speed, wait=False)
            st.rerun()
    else:
        if st.button("🔴 End Call", type="primary", use_container_width=True):
            st.session_state.call_active = False
            agent.reset()
            st.rerun()

# Main Interaction Area
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("💬 Conversation History")
    
    # Chat container
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.conversation:
            if msg["role"] == "agent":
                st.markdown(f'<div class="agent-bubble">🤖 <b>Agent:</b> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="patient-bubble">👤 <b>Patient:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    
    # Controls
    if st.session_state.call_active:
        st.divider()
        col_ctrl1, col_ctrl2 = st.columns([4, 1])
        
        with col_ctrl1:
            can_record = getattr(stt, 'has_hardware', False)
            if not st.session_state.is_recording:
                if st.button("🎙️ Click to Speak", use_container_width=True, disabled=not can_record):
                    st.session_state.is_recording = True
                    st.rerun()
                if not can_record:
                    st.caption("⚠️ Microphone unavailable on cloud server. Use ⌨️ Keyboard mode below.")
            else:
                st.warning("🎤 Recording... Speak now.")
                audio_file = stt.record_audio(duration=3)  # Record for 3 seconds
                st.session_state.is_recording = False
                
                if audio_file:
                    with st.spinner("Transcribing..."):
                        text = stt.transcribe(audio_file)
                        if text:
                            st.session_state.conversation.append({"role": "patient", "content": text})
                            
                            # Process with Agent
                            with st.spinner("Agent thinking..."):
                                response_data = agent.process_user_input(text)
                                agent_msg = response_data.get("agent_message", "I'm sorry, I didn't get that.")
                                st.session_state.conversation.append({"role": "agent", "content": agent_msg})
                                
                                # Check if call should end
                                if response_data.get("action") == "end_call" or response_data.get("action") == "escalate_immediate":
                                    st.session_state.call_active = False
                                
                                # Speak response
                                tts.speak(agent_msg, voice=voice_map[voice_option], speed=speed, wait=False)
                            
                            st.rerun()
        
        with col_ctrl2:
            if st.button("⌨️ Mode"):
                st.session_state.manual_input = True
        
        if st.session_state.get('manual_input'):
            manual_text = st.text_input("Type patient response:")
            if manual_text:
                st.session_state.conversation.append({"role": "patient", "content": manual_text})
                response_data = agent.process_user_input(manual_text)
                agent_msg = response_data.get("agent_message")
                st.session_state.conversation.append({"role": "agent", "content": agent_msg})
                if response_data.get("action") == "end_call":
                    st.session_state.call_active = False
                if getattr(tts, 'has_audio_hardware', False):
                    tts.speak(agent_msg, voice=voice_map[voice_option], speed=speed, wait=False)
                st.session_state.manual_input = False
                st.rerun()

with col_right:
    st.subheader("🧠 Agent Internal State")
    
    if st.session_state.call_active:
        # Profile summary
        profile = agent.context_memory.patient_profile.to_dict()
        with st.expander("👤 Patient Profile", expanded=True):
            if profile['name']: st.write(f"**Name:** {profile['name']}")
            if profile['medications']: st.write(f"**Meds:** {', '.join([m['name'] for m in profile['medications']])}")
            if profile['allergies']: st.write(f"**Allergies:** {', '.join(profile['allergies'])}")
            if profile['weight_history']: st.write(f"**Last Weight:** {profile['weight_history'][-1]['weight']} lbs")
        
        # Edge case detection
        summary = agent.edge_handler.get_edge_case_summary()
        if summary['cases']:
            with st.expander("🛡️ Detected Special Cases", expanded=False):
                for case in summary['cases'][-3:]:
                    st.caption(f"{case['type'].upper()} - Conf: {case['confidence']:.0%}")
                    st.write(case['text'][:50] + "...")
        
        # Decision Logic
        with st.expander("⚡ Decision Logic", expanded=True):
            st.caption("Current Action")
            st.info("Status: " + ("Recording Answer" if agent.call_active else "Call Ending"))
            
            progress = agent.question_controller.get_progress()
            st.metric("Questions Left", progress['pending'])
            
            if agent.edge_handler.escalation_required:
                st.error(f"ESCALATION TRIGGERED: {agent.edge_handler.escalation_reason}")
    else:
        st.info("Start a call to see agent analytics")

# Final Report (Show when call ends)
if not st.session_state.call_active and st.session_state.conversation:
    st.divider()
    st.header("🏢 Healthcare Check-in Summary Report")
    total_data = agent.get_structured_output()
    
    # Top metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        name = total_data.get('patient_info', {}).get('name', 'N/A')
        st.metric("Patient Name", name)
    with m2:
        conf = "✅ Yes" if total_data.get('patient_profile', {}).get('confirmed') else "❌ No"
        st.metric("Identity Verified", conf)
    with m3:
        comp = total_data.get('response_completeness', 0)
        st.metric("Completion", f"{comp:.0%}")
    with m4:
        outcome = total_data.get('outcome', 'completed')
        st.metric("Final Status", outcome.replace('_', ' ').title())

    st.divider()

    report_col1, report_col2 = st.columns([2, 1])
    
    with report_col1:
        st.subheader("📝 Questionnaire Results")
        responses = total_data.get('responses_json', [])
        if responses:
            df = pd.DataFrame(responses)
            # Filter for answered only
            df_answered = df[df['answer'].notna()]
            if not df_answered.empty:
                st.table(df_answered[['question', 'answer']].rename(columns={'question': 'Question', 'answer': 'Captured Answer'}))
            else:
                st.info("No answers captured during this session.")
        
    with report_col2:
        profile = total_data.get('patient_profile', {})
        
        st.subheader("💊 Profile Updates")
        meds = profile.get('medications', [])
        if meds:
            st.write("**Current Medications:**")
            for m in meds: st.write(f"- {m['name']}")
        else:
            st.write("*No medications listed*")
            
        st.subheader("⚠️ Clinical Notes")
        allergies = profile.get('allergies', [])
        if allergies:
            st.error(f"**Allergies:** {', '.join(allergies)}")
        
        vitals = []
        if profile.get('weight_history'):
            v = profile['weight_history'][-1]
            vitals.append(f"⚖️ **Weight:** {v['weight']} {v['units']}")
        if profile.get('bp_history'):
            v = profile['bp_history'][-1]
            vitals.append(f"🩺 **BP:** {v['systolic']}/{v['diastolic']}")
        
        for v in vitals: st.write(v)

    st.divider()
    
    # Download section
    d1, d2 = st.columns(2)
    with d1:
        report_json = json.dumps(total_data, indent=2)
        st.download_button(
            "📥 Download Full JSON Data",
            data=report_json,
            file_name=f"call_report_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )
    with d2:
        pdf_raw = generate_pdf_report(total_data)
        pdf_bytes = bytes(pdf_raw) if isinstance(pdf_raw, bytearray) else pdf_raw
        st.download_button(
            "📄 Export to PDF Report",
            data=pdf_bytes,
            file_name=f"carecaller_summary_{int(time.time())}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Footer
st.divider()
st.caption("Powered by OpenAI Whisper, GPT-4o, and TTS. Built with Streamlit.")
