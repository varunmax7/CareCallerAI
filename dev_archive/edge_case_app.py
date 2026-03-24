# edge_case_app.py
import streamlit as st
from edge_case_handler import EdgeCaseHandler, EdgeCaseType
import pandas as pd
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Edge Case Handler", page_icon="🛡️", layout="wide")

st.title("🛡️ Edge Case Handler")
st.markdown("Handle special scenarios like emergencies, opt-outs, and rescheduling")

# Initialize handler
if 'handler' not in st.session_state:
    st.session_state.handler = EdgeCaseHandler()
    st.session_state.detection_history = []

# Sidebar
with st.sidebar:
    st.header("📊 Statistics")
    
    if st.session_state.detection_history:
        # Count by type
        type_counts = {}
        for detection in st.session_state.detection_history:
            case_type = detection['case_type']
            type_counts[case_type] = type_counts.get(case_type, 0) + 1
        
        # Show counts
        for case_type, count in type_counts.items():
            st.metric(case_type.replace("_", " ").title(), count)
    
    st.divider()
    
    # Reset button
    if st.button("🔄 Reset Handler", type="primary"):
        st.session_state.handler.reset()
        st.session_state.detection_history = []
        st.rerun()
    
    # Escalation status
    escalation_needed, reason = st.session_state.handler.should_escalate()
    if escalation_needed:
        st.error(f"⚠️ Escalation Required!\nReason: {reason}")
    else:
        st.success("✅ No escalation needed")

# Main content - Two columns
col1, col2 = st.columns([1.5, 1])

with col1:
    st.header("🔍 Edge Case Detection")
    
    # Input area
    user_input = st.text_area(
        "Patient message:",
        height=100,
        placeholder="Type what the patient says...",
        key="edge_input"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔍 Detect Edge Case", type="primary"):
            if user_input:
                result = st.session_state.handler.detect_edge_case(user_input)
                
                if result:
                    st.session_state.detection_history.append({
                        "input": user_input,
                        "case_type": result.case_type.value,
                        "confidence": result.confidence,
                        "response": result.response,
                        "action": result.action,
                        "timestamp": pd.Timestamp.now()
                    })
                    st.session_state.last_result = result
                    st.rerun()
                else:
                    st.info("No edge case detected")
    
    with col_btn2:
        if st.button("🧪 Quick Test"):
            st.session_state.show_test_panel = True
    
    with col_btn3:
        if st.button("🗑️ Clear"):
            st.session_state.last_result = None
            st.rerun()
    
    # Display detection result
    if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
        result = st.session_state.last_result
        
        # Color based on severity
        if result.case_type in [EdgeCaseType.EMERGENCY, EdgeCaseType.COMPLAINT]:
            st.error(f"🚨 **{result.case_type.value.upper()} DETECTED**")
        elif result.case_type in [EdgeCaseType.MEDICAL_ADVICE, EdgeCaseType.PRICING]:
            st.warning(f"⚠️ **{result.case_type.value.upper()} DETECTED**")
        else:
            st.info(f"ℹ️ **{result.case_type.value.upper()} DETECTED**")
        
        col_met1, col_met2, col_met3 = st.columns(3)
        with col_met1:
            st.metric("Confidence", f"{result.confidence:.0%}")
        with col_met2:
            st.metric("Action", result.action.replace("_", " ").title())
        with col_met3:
            st.metric("Escalate", "Yes" if result.needs_human else "No")
        
        st.subheader("💬 Agent Response")
        st.info(result.response)
        
        if result.extracted_data:
            st.subheader("📋 Extracted Data")
            st.json(result.extracted_data)
    
    # Test scenarios panel
    if st.session_state.get('show_test_panel', False):
        with st.expander("🧪 Test Scenarios", expanded=True):
            st.subheader("Quick Test Scenarios")
            
            test_scenarios = [
                ("🚫 Opt Out", "I don't want to continue"),
                ("📅 Reschedule", "Can we reschedule for tomorrow at 2pm?"),
                ("❌ Wrong Number", "You have the wrong number"),
                ("💊 Medical Advice", "Should I take this with food?"),
                ("🚨 Emergency", "I'm having chest pain"),
                ("💰 Pricing", "How much does this cost?"),
                ("😤 Complaint", "I want to speak to a manager"),
                ("📞 Technical", "I can't hear you clearly")
            ]
            
            cols = st.columns(2)
            for i, (label, text) in enumerate(test_scenarios):
                with cols[i % 2]:
                    if st.button(label, use_container_width=True):
                        result = st.session_state.handler.detect_edge_case(text)
                        if result:
                            st.session_state.detection_history.append({
                                "input": text,
                                "case_type": result.case_type.value,
                                "confidence": result.confidence,
                                "response": result.response,
                                "action": result.action,
                                "timestamp": pd.Timestamp.now()
                            })
                            st.session_state.last_result = result
                            st.rerun()

with col2:
    st.header("📊 Detection History")
    
    if st.session_state.detection_history:
        # Create dataframe
        df = pd.DataFrame(st.session_state.detection_history)
        
        # Show recent detections
        for idx, row in df.tail(5).iterrows():
            with st.container():
                # Color coding
                if row['case_type'] == 'emergency':
                    st.error(f"🚨 **{row['case_type'].upper()}**")
                elif row['case_type'] in ['medical_advice', 'pricing']:
                    st.warning(f"⚠️ **{row['case_type'].replace('_', ' ').title()}**")
                else:
                    st.info(f"ℹ️ **{row['case_type'].replace('_', ' ').title()}**")
                
                st.caption(f"Confidence: {row['confidence']:.0%} | Action: {row['action']}")
                st.write(f"\"{row['input'][:100]}...\"")
                st.divider()
        
        # Export button
        if st.button("📥 Export History"):
            st.download_button(
                label="Download JSON",
                data=df.to_json(indent=2),
                file_name="edge_case_history.json",
                mime="application/json"
            )
    else:
        st.info("No edge cases detected yet")

# Priority Visualization
st.divider()
st.header("⚡ Edge Case Priority Levels")

priority_data = []
for case_type in EdgeCaseType:
    priority = st.session_state.handler.get_priority(case_type)
    priority_data.append({
        "Case Type": case_type.value.replace("_", " ").title(),
        "Priority": priority,
        "Urgency": "High" if priority >= 70 else "Medium" if priority >= 40 else "Low"
    })

df_priority = pd.DataFrame(priority_data)

# Create bar chart
fig = go.Figure(data=[
    go.Bar(
        x=df_priority["Case Type"],
        y=df_priority["Priority"],
        marker_color=[100 if p >= 70 else 50 if p >= 40 else 20 for p in df_priority["Priority"]],
        text=df_priority["Priority"],
        textposition='auto',
    )
])
fig.update_layout(
    title="Edge Case Priority Levels",
    xaxis_title="Case Type",
    yaxis_title="Priority (0-100)",
    height=400,
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# Response Templates
with st.expander("📝 Response Templates"):
    st.subheader("Agent Response Templates")
    
    for case_type in EdgeCaseType:
        responses = st.session_state.handler.responses.get(case_type, [])
        if responses:
            with st.container():
                st.write(f"**{case_type.value.replace('_', ' ').title()}:**")
                for resp in responses:
                    st.caption(f"• {resp}")

# Safety Rules
with st.expander("🔒 Safety Rules"):
    st.markdown("""
    ### Prohibited Content
    
    The agent must NEVER:
    - Give medical advice
    - Recommend medications
    - Diagnose conditions
    - Prescribe treatments
    
    ### Escalation Triggers
    
    Immediate human escalation required for:
    - Emergency symptoms (chest pain, breathing difficulty)
    - Severe complaints or anger
    - Medical emergencies
    - Requests for medical advice
    
    ### Safe Responses
    
    Always redirect to:
    - Doctor for medical questions
    - Pharmacy for pricing
    - Supervisor for complaints
    - Emergency services for urgent issues
    """)

# Footer
st.divider()
st.caption("💡 Edge cases are automatically detected and handled with appropriate responses")
