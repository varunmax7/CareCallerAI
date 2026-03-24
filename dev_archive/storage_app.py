# storage_app.py
import streamlit as st
import pandas as pd
import json
from response_storage import ResponseStorage, AnswerConfidence, Answer
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Response Storage", page_icon="💾", layout="wide")

st.title("Structured Response Storage")
st.markdown("Save and export answers in training data format")

# Initialize storage
if 'storage' not in st.session_state:
    st.session_state.storage = ResponseStorage()

# Sidebar
with st.sidebar:
    st.header("Call Information")
    
    st.metric("Call ID", st.session_state.storage.call_id)
    
    # Duration
    duration = (datetime.now() - st.session_state.storage.start_time).seconds
    st.metric("Duration", f"{duration}s")
    
    st.divider()
    
    # Completeness
    completeness = st.session_state.storage.get_completeness_score()
    st.metric("Completeness", f"{completeness:.1%}")
    
    # Quality
    quality = st.session_state.storage.get_quality_score()
    st.metric("Quality Score", f"{quality:.1%}")
    
    st.divider()
    
    # Export buttons
    st.subheader("Export")
    
    if st.button("Export to JSON", type="primary"):
        filename = f"{st.session_state.storage.call_id}.json"
        st.session_state.storage.export_to_json(filename)
        with open(filename, 'r') as f:
            st.download_button(
                label="Download JSON",
                data=f,
                file_name=filename,
                mime="application/json"
            )
    
    if st.button("Export to CSV"):
        filename = f"{st.session_state.storage.call_id}_responses.csv"
        st.session_state.storage.export_to_csv(filename)
        with open(filename, 'r') as f:
            st.download_button(
                label="Download CSV",
                data=f,
                file_name=filename,
                mime="text/csv"
            )
    
    st.divider()
    
    # Reset button
    if st.button("New Call", type="secondary"):
        st.session_state.storage = ResponseStorage()
        st.rerun()

# Main content - Three columns
col1, col2, col3 = st.columns([1.5, 1.5, 1])

with col1:
    st.header("Question Responses")
    
    # Show all questions with answers
    for q_id, answer in st.session_state.storage.answers.items():
        with st.container():
            # Color coding based on confidence
            if answer.answer:
                if answer.confidence == AnswerConfidence.HIGH:
                    bg_color = "#90EE90"
                elif answer.confidence == AnswerConfidence.MEDIUM:
                    bg_color = "#FFE4B5"
                else:
                    bg_color = "#FFB6C1"
            else:
                bg_color = "#F0F0F0"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; color: black;">
                <b>Q{answer.question_id}: {answer.question_text}</b><br>
                <b>Answer:</b> {answer.answer or 'Not answered'}<br>
                <b>Confidence:</b> {answer.confidence_score:.0%} ({answer.confidence.value})<br>
                <b>Source:</b> {answer.source or '-'}
            </div>
            """, unsafe_allow_html=True)
    
    # Add custom answer
    with st.expander("Add Custom Answer"):
        q_id = st.number_input("Question ID", min_value=1, max_value=100, value=15)
        q_text = st.text_input("Question Text", "Custom question")
        answer_text = st.text_area("Answer")
        
        if st.button("Add Answer"):
            st.session_state.storage.add_answer(
                question_id=q_id,
                answer=answer_text,
                confidence=AnswerConfidence.HIGH,
                confidence_score=0.8,
                source="manual"
            )
            st.rerun()

with col2:
    st.header("Analytics")
    
    # Donut chart for completeness
    answered = len(st.session_state.storage.get_answered_questions())
    missing = len(st.session_state.storage.get_missing_questions())
    
    fig = go.Figure(data=[go.Pie(
        labels=['Answered', 'Missing'],
        values=[answered, missing],
        hole=.3,
        marker_colors=['#00ff00', '#ff4444']
    )])
    fig.update_layout(height=300, title="Response Completeness")
    st.plotly_chart(fig, use_container_width=True)
    
    # Confidence distribution
    confidence_levels = {
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "Missing": 0
    }
    
    for answer in st.session_state.storage.answers.values():
        if answer.answer is None:
            confidence_levels["Missing"] += 1
        elif answer.confidence == AnswerConfidence.HIGH:
            confidence_levels["High"] += 1
        elif answer.confidence == AnswerConfidence.MEDIUM:
            confidence_levels["Medium"] += 1
        else:
            confidence_levels["Low"] += 1
    
    fig2 = go.Figure(data=[go.Bar(
        x=list(confidence_levels.keys()),
        y=list(confidence_levels.values()),
        marker_color=['#00ff00', '#ffaa00', '#ff4444', '#cccccc']
    )])
    fig2.update_layout(height=300, title="Confidence Distribution")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Issues
    st.subheader("Issues Flagged")
    issues = st.session_state.storage.flag_issues()
    if issues:
        for issue in issues:
            st.error(f"• {issue}")
    else:
        st.success("No issues detected")
    
    # Recommendations
    recommendations = st.session_state.storage.generate_summary().get("recommendations", [])
    if recommendations:
        st.subheader("Recommendations")
        for rec in recommendations:
            st.info(f"• {rec}")

with col3:
    st.header("Conversation Log")
    
    # Show conversation history
    if st.session_state.storage.conversation_history:
        for msg in st.session_state.storage.conversation_history[-10:]:
            role_icon = "🤖" if msg["role"] == "agent" else "👤"
            st.caption(f"{role_icon} **{msg['role'].upper()}** - {msg['timestamp'][:19]}")
            st.write(msg["content"][:100])
            st.divider()
    else:
        st.info("No conversation logged yet")
    
    # Add conversation turn
    with st.expander("Add Conversation Turn"):
        role = st.selectbox("Role", ["patient", "agent"])
        content = st.text_area("Message")
        
        if st.button("Add Turn"):
            st.session_state.storage.add_conversation_turn(role, content)
            st.rerun()
    
    # Show missing questions
    st.subheader("Missing Questions")
    missing_questions = st.session_state.storage.get_missing_questions()
    for q in missing_questions:
        st.warning(f"Q{q.question_id}: {q.question_text}")

# Bottom section - Export Preview
st.divider()
with st.expander("JSON Export Preview (Training Data Format)"):
    record = st.session_state.storage.to_json()
    st.json(record)

with st.expander("Summary Report"):
    summary = st.session_state.storage.generate_summary()
    st.json(summary)

# Validation section
with st.expander("Training Data Format Validation"):
    validation = st.session_state.storage.validate_against_training_format()
    
    if validation["valid"]:
        st.success("Output matches training data format")
    else:
        st.error("Validation issues found")
        if validation.get("missing_fields"):
            st.write("Missing fields:", validation["missing_fields"])

# Footer
st.divider()
st.caption(f"Call ID: {st.session_state.storage.call_id} | Ready for export")
