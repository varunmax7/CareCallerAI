# validation_app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from validation_system import ValidationSystem, ValidationSeverity
import json

st.set_page_config(page_title="Validation System", page_icon="✅", layout="wide")

st.title("Call Quality Validation System")
st.markdown("Verify call quality and generate comprehensive reports")

# Initialize validation system
if 'validator' not in st.session_state:
    st.session_state.validator = ValidationSystem()
if 'last_report' not in st.session_state:
    st.session_state.last_report = None

# Sidebar
with st.sidebar:
    st.header("Validation Criteria")
    
    st.subheader("Required Checks")
    st.markdown("""
    ✅ All 14 questions attempted  
    ✅ Answer format validation  
    ✅ No medical advice  
    ✅ Duration within range  
    ✅ Data quality check  
    ✅ Compliance check
    """)
    
    st.divider()
    
    st.subheader("Severity Levels")
    colors = {
        "critical": "🔴 Critical",
        "high": "🟠 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
        "info": "ℹ️ Info"
    }
    for severity, label in colors.items():
        st.markdown(f"{label}")
    
    st.divider()
    
    if st.button("Export Validation Report", type="primary"):
        if st.session_state.last_report:
            report_dict = st.session_state.last_report.to_dict()
            st.download_button(
                label="Download JSON",
                data=json.dumps(report_dict, indent=2),
                file_name=f"validation_{st.session_state.last_report.call_id}.json",
                mime="application/json"
            )

# Main content - Two columns
col1, col2 = st.columns([1, 1.5])

with col1:
    st.header("Call Data Input")
    
    # Input method selection
    input_method = st.radio("Input Method", ["Manual Entry", "JSON Upload", "Example Call"])
    
    if input_method == "Manual Entry":
        call_id = st.text_input("Call ID", "CALL_001")
        duration = st.number_input("Duration (seconds)", min_value=0, max_value=3600, value=120)
        
        transcript = st.text_area(
            "Transcript",
            height=200,
            placeholder="[AGENT]: ...\n[USER]: ..."
        )
        
        # Quick add responses
        st.subheader("Responses")
        responses = []
        cols = st.columns(2)
        for i in range(14):
            with cols[i % 2]:
                q_text = st.text_input(f"Q{i+1}", key=f"q_{i}", placeholder=f"Question {i+1}")
                answer = st.text_input(f"Answer {i+1}", key=f"a_{i}")
                if q_text and answer:
                    responses.append({"question": q_text, "answer": answer})
        
        if st.button("Validate Call", type="primary"):
            call_data = {
                "call_id": call_id,
                "call_duration": duration,
                "transcript_text": transcript,
                "responses_json": responses
            }
            report = st.session_state.validator.validate_call(call_data)
            st.session_state.last_report = report
            st.rerun()
    
    elif input_method == "JSON Upload":
        uploaded_file = st.file_uploader("Upload call data JSON", type=["json"])
        if uploaded_file:
            call_data = json.load(uploaded_file)
            if st.button("Validate Call", type="primary"):
                report = st.session_state.validator.validate_call(call_data)
                st.session_state.last_report = report
                st.rerun()
    
    else:  # Example Call
        st.info("Using example call data")
        if st.button("Validate Example Call"):
            example_call = {
                "call_id": "EXAMPLE_CALL_001",
                "call_duration": 180,
                "transcript_text": """
[AGENT]: Hello, this is CareCaller. What is your weight?
[USER]: 185 pounds
[AGENT]: Any side effects?
[USER]: No
[AGENT]: Any allergies?
[USER]: No
[AGENT]: Taking medication as prescribed?
[USER]: Yes
""",
                "responses_json": [
                    {"question": "Weight", "answer": "185 pounds"},
                    {"question": "Side effects", "answer": "No"},
                    {"question": "Allergies", "answer": "No"},
                    {"question": "Medication taken", "answer": "Yes"}
                ]
            }
            report = st.session_state.validator.validate_call(example_call)
            st.session_state.last_report = report
            st.rerun()

with col2:
    st.header("Validation Results")
    
    if st.session_state.last_report:
        report = st.session_state.last_report
        
        # Score gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = report.overall_score,
            title = {'text': "Quality Score"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen" if report.overall_score >= 70 else "orange"},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 70], 'color': "orange"},
                    {'range': [70, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Status
        if report.is_valid:
            st.success(f"CALL PASSED - Score: {report.overall_score:.1f}/100")
        else:
            st.error(f"CALL NEEDS REVIEW - Score: {report.overall_score:.1f}/100")
        
        if report.ticket_needed:
            st.warning(f"Review Ticket Needed")
            st.info(f"Category: {report.ticket_category}")
        
        st.divider()
        
        # Metrics
        st.subheader("Call Metrics")
        metrics = report.metrics
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Questions", f"{metrics['questions_answered']}/14")
        with col_m2:
            st.metric("Completeness", f"{metrics['completeness_score']:.0%}")
        with col_m3:
            st.metric("Duration", f"{metrics['call_duration_seconds']}s")
        with col_m4:
            st.metric("Valid Answers", f"{metrics['questions_valid']}")
        
        # Issues
        if report.issues:
            st.subheader(f"Issues ({len(report.issues)})")
            
            for issue in report.issues:
                with st.expander(f"[{issue.severity.value.upper()}] {issue.description}"):
                    st.write(f"**Type:** {issue.issue_type}")
                    st.write(f"**Category:** {issue.category.value}")
                    if issue.location:
                        st.write(f"**Location:** {issue.location}")
                    if issue.details:
                        st.write(f"**Details:** {issue.details}")
                    if issue.recommendation:
                        st.info(f"💡 {issue.recommendation}")
        
        # Recommendations
        if report.recommendations:
            st.subheader("Recommendations")
            for rec in report.recommendations:
                st.info(f"• {rec}")
        
        # Post-call summary
        with st.expander("Post-Call Summary"):
            summary = st.session_state.validator.generate_post_call_summary(report)
            st.code(summary, language="text")
        
        # Export
        st.download_button(
            label="Download Full Report",
            data=json.dumps(report.to_dict(), indent=2),
            file_name=f"validation_report_{report.call_id}.json",
            mime="application/json"
        )
        
    else:
        st.info("Enter call data or upload JSON to validate")

# Bottom section - Validation rules
st.divider()
with st.expander("Validation Rules Reference"):
    st.markdown("""
    ### Question Coverage
    - All 14 required questions must be attempted
    - Missing >3 questions creates high severity issue
    
    ### Answer Format Validation
    | Question Type | Expected Format | Example |
    |--------------|----------------|---------|
    | Weight | Number with unit | "185 pounds" |
    | Blood Pressure | Systolic/Diastolic | "120/80" |
    | Yes/No | Clear yes/no | "Yes", "No" |
    | Date | Specific day | "Monday", "Tomorrow" |
    
    ### Prohibited Agent Behaviors
    - Medical advice: "You should take..."
    - Unprofessional language
    - Requesting sensitive information (SSN, payment)
    
    ### Ticket Triggers
    - Critical violation (medical advice)
    - Multiple high severity issues
    - Completeness < 60%
    - >3 unclear answers
    
    ### Scoring
    - Start at 100
    - Critical issue: -30
    - High severity: -15
    - Medium severity: -8
    - Low severity: -3
    - Completeness bonus: +10%
    - Quality bonus: +10%
    """)

# Footer
st.divider()
st.caption("Validation system checks call quality against requirements")
