# final_integrated_agent.py
import streamlit as st
import os
from dotenv import load_dotenv
from agent_core import VoiceAgent
from tts_engine import TTSEngine
from stt_engine import STTEngine
from context_memory import ContextMemory
from question_controller import QuestionFlowController
from edge_case_handler import EdgeCaseHandler
from response_storage import ResponseStorage
from validation_system import ValidationSystem
import json

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Complete Voice Agent", page_icon="🤖", layout="wide")

st.title("CareCaller Complete Voice Agent")
st.markdown("AI-powered healthcare validation call system")

# Initialize all components
def initialize_state():
    st.session_state.agent = VoiceAgent(api_key)
    st.session_state.tts = TTSEngine(api_key)
    st.session_state.stt = STTEngine(api_key)
    st.session_state.messages = []
    st.session_state.call_active = False

# Check for required state keys
required_keys = ['agent', 'tts', 'stt', 'messages', 'call_active']
if not all(key in st.session_state for key in required_keys):
    initialize_state()

# Sidebar
with st.sidebar:
    st.header("App Management")
    if st.button("🔄 Reset App State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    st.header("Call Controls")
    
    if not st.session_state.call_active:
        if st.button("Start New Call", type="primary"):
            st.session_state.call_active = True
            st.session_state.messages = []
            st.session_state.agent.reset()
            # Initial greeting
            response = st.session_state.agent.process_user_input("")
            greeting = response['agent_message']
            st.session_state.messages.append({"role": "agent", "content": greeting})
            st.session_state.tts.speak(greeting, wait=False)
            st.rerun()
    else:
        if st.button("End Call", type="primary"):
            st.session_state.call_active = False
            st.rerun()
    
    st.divider()
    
    st.header("Call Status")
    progress = st.session_state.agent.question_controller.get_progress()
    st.metric("Questions Completed", f"{progress['answered']}/14")
    st.progress(progress['completion_rate'])
    
    st.divider()
    
    st.header("Export")
    if st.button("Export Call Data"):
        record = st.session_state.agent.storage.to_json()
        st.download_button(
            label="Download JSON",
            data=json.dumps(record, indent=2),
            file_name=f"{st.session_state.agent.storage.call_id}.json",
            mime="application/json"
        )

# Main content - Three columns
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.header("Conversation")
    
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "agent":
                st.chat_message("assistant").write(msg["content"])
            else:
                st.chat_message("user").write(msg["content"])
    
    if st.session_state.call_active:
        user_input = st.chat_input("Speak or type your response...")
        
        # Voice Input Button
        voice_col1, voice_col2 = st.columns([1, 4])
        with voice_col1:
            if st.button("🎙️ Speak"):
                with st.spinner("Listening... (5s)"):
                    # Record for 5 seconds
                    voice_text = st.session_state.stt.record_and_transcribe(duration=5)
                    if voice_text:
                        user_input = voice_text
                    else:
                        st.error("Could not capture speech. Please try again or type.")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process with agent
            response = st.session_state.agent.process_user_input(user_input)
            
            # Add agent response
            st.session_state.messages.append({"role": "agent", "content": response['agent_message']})
            
            # Speak response
            st.session_state.tts.speak(response['agent_message'], wait=False)
            
            # Check if call was ended by agent
            if response.get("action") == "end_call" or response.get("action") == "escalate_immediate":
                st.session_state.call_active = False
                
            st.rerun()

with col2:
    st.header("Question Progress")
    
    progress = st.session_state.agent.question_controller.get_progress()
    
    # Show next question
    next_q = st.session_state.agent.question_controller.get_next_question(mark_as_asked=False)
    if next_q:
        st.info(f"**Next Question:** {next_q.question_text}")
    
    # Show answered questions
    with st.expander("Answered Questions", expanded=True):
        for q in progress['answered_questions'][-5:]:
            st.write(f"✅ **{q['category']}:** {q['answer'][:50]}")
    
    # Show missing categories
    if progress['remaining_categories']:
        st.warning(f"Missing: {', '.join(progress['remaining_categories'][:3])}")

with col3:
    st.header("Shield & Validation")
    
    # Show recent edge cases
    if st.session_state.agent.edge_handler.detected_cases:
        with st.expander("Detected Edge Cases", expanded=True):
            for case in st.session_state.agent.edge_handler.detected_cases[-3:]:
                st.write(f"⚠️ **{case['type']}** (conf: {case['confidence']:.0%})")
                st.caption(case['text'][:50])
    
    # Show validation status
    if st.session_state.messages:
        if st.button("Validate Call Quality"):
            # Build call data
            call_data = st.session_state.agent.storage.to_json()
            report = st.session_state.agent.validator.validate_call(call_data)
            st.session_state.last_validation = report
            
            if report.ticket_needed:
                st.error(f"Review Ticket Needed: {report.ticket_category}")
            else:
                st.success("Call passed validation!")
            
            st.info(f"Quality Score: {report.overall_score:.1f}/100")

# Bottom section
st.divider()
with st.expander("Call Summary & Validation Report"):
    if hasattr(st.session_state, 'last_validation') and st.session_state.last_validation:
        report = st.session_state.last_validation
        summary = st.session_state.agent.validator.generate_post_call_summary(report)
        st.code(summary, language="text")
    else:
        st.info("Click 'Validate Call Quality' to generate report")

st.caption("🤖 Voice Agent | 🎤 Speech-to-Text | 🔊 Text-to-Speech | ✅ Validation Ready")
