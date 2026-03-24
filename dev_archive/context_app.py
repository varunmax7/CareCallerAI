# context_app.py
import streamlit as st
from context_memory import ContextMemory, TopicCategory
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(page_title="Context Memory", page_icon="🧠", layout="wide")

st.title("🧠 Context Memory System")
st.markdown("Remember what was discussed and maintain coherent conversation")

# Initialize memory
if 'memory' not in st.session_state:
    st.session_state.memory = ContextMemory()
    st.session_state.conversation_display = []

# Sidebar
with st.sidebar:
    st.header("📊 Memory Stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.memory.messages))
    with col2:
        st.metric("Topics Covered", 
                  sum(1 for t in st.session_state.memory.get_topic_status().values() 
                      if t['covered']))
    
    st.divider()
    
    # Reset button
    if st.button("🔄 Reset Memory", type="primary"):
        st.session_state.memory.reset()
        st.session_state.conversation_display = []
        st.rerun()
    
    # Export button
    if st.button("📥 Export Context"):
        context_dict = st.session_state.memory.to_dict()
        st.download_button(
            label="Download JSON",
            data=json.dumps(context_dict, indent=2),
            file_name=f"context_{st.session_state.memory.session_id}.json",
            mime="application/json"
        )

# Main content - Three columns
col1, col2, col3 = st.columns([2, 1.5, 1.5])

with col1:
    st.header("💬 Conversation")
    
    # Display conversation
    for msg in st.session_state.conversation_display:
        if msg["role"] == "agent":
            st.chat_message("assistant").write(msg["content"])
        else:
            st.chat_message("user").write(msg["content"])
    
    # Input area
    col_input1, col_input2 = st.columns([4, 1])
    
    with col_input1:
        user_input = st.text_input(
            "Patient response:",
            key="user_input",
            placeholder="Type what the patient says..."
        )
    
    with col_input2:
        role = st.selectbox("Role", ["patient", "agent"], key="role_select")
    
    if st.button("📝 Add Message", type="primary"):
        if user_input:
            # Add to memory
            message = st.session_state.memory.add_message(role, user_input)
            
            # Add to display
            st.session_state.conversation_display.append({
                "role": role,
                "content": user_input,
                "topic": message.topic.value if message.topic else None,
                "intent": message.intent,
                "importance": message.importance
            })
            
            st.rerun()
    
    # Quick test scenarios
    st.divider()
    st.subheader("🧪 Test Scenarios")
    
    scenarios = {
        "Normal Call": [
            ("agent", "Hello, this is CareCaller. Am I speaking with John?"),
            ("patient", "Yes, this is John."),
            ("agent", "How are you feeling today?"),
            ("patient", "I'm doing well, thanks.")
        ],
        "Topic Switch": [
            ("agent", "Have you experienced any side effects?"),
            ("patient", "No side effects. But how much does this cost?"),
            ("agent", "I understand. Let me transfer you to billing."),
            ("patient", "Actually, wait, I do have a question about dosage.")
        ],
        "Info Extraction": [
            ("patient", "I'm 185 pounds and my blood pressure is 120 over 80."),
            ("patient", "I'm allergic to penicillin."),
            ("patient", "I take lisinopril every morning.")
        ],
        "Emergency": [
            ("patient", "I'm having chest pain!"),
            ("agent", "This sounds serious. I'm escalating immediately."),
        ]
    }
    
    scenario_cols = st.columns(2)
    for i, (scenario_name, messages) in enumerate(scenarios.items()):
        with scenario_cols[i % 2]:
            if st.button(scenario_name, use_container_width=True):
                for role, content in messages:
                    message = st.session_state.memory.add_message(role, content)
                    st.session_state.conversation_display.append({
                        "role": role,
                        "content": content,
                        "topic": message.topic.value if message.topic else None
                    })
                st.rerun()

with col2:
    st.header("👤 Patient Profile")
    
    profile = st.session_state.memory.patient_profile.to_dict()
    
    if profile["name"]:
        st.success(f"**Name:** {profile['name']}")
    else:
        st.info("Name not yet collected")
    
    if profile["medications"]:
        with st.expander("💊 Medications", expanded=True):
            for med in profile["medications"][-3:]:
                st.write(f"- {med['name']}")
    
    if profile["allergies"]:
        with st.expander("⚠️ Allergies", expanded=True):
            for allergy in profile["allergies"]:
                st.write(f"- {allergy}")
    
    if profile["weight_history"]:
        with st.expander("⚖️ Weight History"):
            for weight in profile["weight_history"][-3:]:
                st.write(f"- {weight['weight']} {weight['units']} ({weight['date'][:10]})")
    
    if profile["bp_history"]:
        with st.expander("❤️ Blood Pressure"):
            for bp in profile["bp_history"][-3:]:
                st.write(f"- {bp['systolic']}/{bp['diastolic']} ({bp['date'][:10]})")
    
    if profile["notes"]:
        with st.expander("📝 Notes"):
            for note in profile["notes"][-3:]:
                st.write(f"- {note}")
    
    # Update time
    st.caption(f"Last updated: {profile['updated_at'][:19]}")

with col3:
    st.header("📚 Context & Topics")
    
    # Topic coverage visualization
    status = st.session_state.memory.get_topic_status()
    
    # Prepare data for chart
    topics = list(status.keys())
    covered = [1 if s['covered'] else 0 for s in status.values()]
    confidence = [s['confidence'] for s in status.values()]
    
    fig = go.Figure(data=[
        go.Bar(name='Covered', x=topics, y=covered, marker_color='green'),
        go.Bar(name='Confidence', x=topics, y=confidence, marker_color='blue')
    ])
    fig.update_layout(
        title="Topic Coverage",
        xaxis_title="Topics",
        yaxis_title="Status",
        height=300,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Uncovered topics
    uncovered = st.session_state.memory.get_uncovered_topics()
    if uncovered:
        st.warning(f"**Still to cover:** {', '.join(uncovered[:5])}")
    
    # Recent messages
    st.subheader("📝 Recent Context")
    recent = st.session_state.memory.get_recent_context(5)
    for msg in recent:
        with st.container():
            role_icon = "🤖" if msg.role == "agent" else "👤"
            st.caption(f"{role_icon} **{msg.role.upper()}** - {msg.topic.value if msg.topic else 'general'} - {msg.importance:.0%}")
            st.write(msg.content[:80])
    
    # Topic switches
    switches = st.session_state.memory.get_topic_switches_summary()
    if switches:
        st.subheader("🔄 Recent Topic Switches")
        for switch in switches[-3:]:
            st.caption(f"{switch['from']} → {switch['to']}")
            st.write(f"\"{switch['message'][:60]}...\"")
    
    # Off-topic queue
    off_topic = st.session_state.memory.get_off_topic_queue()
    if off_topic:
        with st.expander("📋 Off-Topic Messages"):
            for item in off_topic:
                st.write(f"**{item['topic']}:** {item['content'][:100]}")

# Conversation summary at bottom
st.divider()
with st.expander("📄 Full Conversation Summary"):
    st.write(st.session_state.memory.get_context_for_llm())
    
    # Display as JSON
    if st.button("Show Raw JSON"):
        st.json(st.session_state.memory.to_dict())

# Footer
st.caption("💡 Tip: Context memory tracks topics, extracts information, and handles topic switches automatically")
