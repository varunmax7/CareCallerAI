# agent_app.py
import streamlit as st
import json
from dotenv import load_dotenv
import os
from agent_core import VoiceAgent

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="CareCaller Agent", page_icon="🤖", layout="wide")

st.title("🤖 AI Voice Agent - The Brain")
st.markdown("Healthcare medication refill assistant")

# Initialize agent in session state
if 'agent' not in st.session_state:
    if not api_key:
        st.error("❌ OPENAI_API_KEY not found in .env file")
        st.stop()
    st.session_state.agent = VoiceAgent(api_key)
    st.session_state.messages = []
    st.session_state.call_started = False

# Sidebar - Agent Controls
with st.sidebar:
    st.header("🎮 Agent Controls")
    
    if st.button("🔄 Reset Call", type="primary"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.session_state.call_started = False
        st.rerun()
    
    st.divider()
    
    st.header("📊 Call Progress")
    completion = st.session_state.agent.get_completion_status()
    
    # Progress bar
    st.progress(completion['completion_rate'])
    st.metric("Questions Completed", f"{completion['answered']}/{completion['total_questions']}")
    
    if completion['missing_categories']:
        st.warning(f"Missing: {', '.join(completion['missing_categories'][:3])}")
    
    st.divider()
    
    st.header("ℹ️ Patient Info")
    st.json(st.session_state.agent.patient_info)
    
    st.divider()
    
    st.header("🎯 Actions")
    action = st.selectbox("Trigger Edge Case", ["None", "Opt-out", "Reschedule", "Wrong Number", "Emergency"])
    
    if action != "None":
        if st.button("Trigger"):
            # Simulate edge case
            edge_map = {
                "Opt-out": "I want to opt out of these calls",
                "Reschedule": "Can we reschedule for tomorrow?",
                "Wrong Number": "You have the wrong number",
                "Emergency": "I'm having chest pain"
            }
            response = st.session_state.agent.process_user_input(edge_map[action])
            st.session_state.messages.append({"role": "user", "content": edge_map[action]})
            st.session_state.messages.append({"role": "agent", "content": response['agent_message']})
            st.rerun()

# Main chat interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Conversation")
    
    # Display chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])
    
    # Input area
    if not st.session_state.call_started:
        if st.button("📞 Start Call", type="primary"):
            st.session_state.call_started = True
            # Initial greeting
            greeting = st.session_state.agent.process_user_input("")
            st.session_state.messages.append({"role": "agent", "content": greeting['agent_message']})
            st.rerun()
    else:
        # Text input for simulation
        user_input = st.chat_input("Patient response (or type here for testing)...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process with agent
            response = st.session_state.agent.process_user_input(user_input)
            
            # Add agent response
            st.session_state.messages.append({"role": "agent", "content": response['agent_message']})
            
            # Check if call ended
            if not st.session_state.agent.call_active:
                st.success("✅ Call completed!")
                st.balloons()
            
            st.rerun()

with col2:
    st.header("📝 Structured Data")
    
    # Show collected answers
    if st.session_state.agent.responses_json:
        st.subheader("Collected Answers")
        for answer in st.session_state.agent.responses_json:
            with st.expander(f"❓ {answer['category'].title()}"):
                st.write(f"**Q:** {answer['question']}")
                st.write(f"**A:** {answer['answer']}")
                st.write(f"**Confidence:** {answer['confidence']:.0%}")
    else:
        st.info("No answers collected yet")
    
    # Show next question
    completion = st.session_state.agent.get_completion_status()
    if completion['answered'] < completion['total_questions']:
        st.divider()
        st.info(f"**Next:** {st.session_state.agent.questions[completion['answered']]['question']}")

# Footer with status
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🎯 Status: {'Active' if st.session_state.agent.call_active else 'Completed'}")
with col2:
    st.caption(f"📊 Model: {st.session_state.agent.model}")
with col3:
    st.caption(f"🔄 Total exchanges: {len(st.session_state.messages) // 2}")

# Export button
if st.session_state.agent.responses_json:
    if st.button("📥 Export Structured Data"):
        output = st.session_state.agent.get_structured_output()
        st.download_button(
            label="Download JSON",
            data=json.dumps(output, indent=2),
            file_name="call_output.json",
            mime="application/json"
        )
