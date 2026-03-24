# question_app.py
import streamlit as st
from question_controller import QuestionFlowController, QuestionStatus
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Question Flow Controller", page_icon="📋", layout="wide")

st.title("📋 Question Flow Controller")
st.markdown("Manage the 14-question health checklist with intelligent flow")

# Initialize controller
if 'controller' not in st.session_state:
    st.session_state.controller = QuestionFlowController()
    st.session_state.current_response = ""
    st.session_state.conversation = []

# Sidebar
with st.sidebar:
    st.header("📊 Progress")
    
    progress = st.session_state.controller.get_progress()
    
    # Progress circle
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Answered", f"{progress['answered']}/{progress['total_questions']}")
    with col2:
        st.metric("Completion", f"{progress['completion_rate']*100:.0f}%")
    
    # Progress bar
    st.progress(progress['completion_rate'])
    
    # Categories
    st.subheader("📁 Categories")
    st.write(f"Completed: {progress['categories_completed']}/{progress['total_categories']}")
    
    if progress['remaining_categories']:
        st.warning(f"Remaining: {', '.join(progress['remaining_categories'])}")
    
    st.divider()
    
    # Reset button
    if st.button("🔄 Reset All Questions", type="primary"):
        st.session_state.controller.reset()
        st.session_state.conversation = []
        st.rerun()
    
    # Export data
    if progress['answered'] > 0:
        if st.button("📥 Export Responses"):
            responses = st.session_state.controller.get_structured_responses()
            st.download_button(
                label="Download JSON",
                data=pd.DataFrame(responses).to_json(indent=2),
                file_name="question_responses.json",
                mime="application/json"
            )

# Main content - Two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Question Flow")
    
    # Display conversation
    for msg in st.session_state.conversation:
        if msg["role"] == "agent":
            st.chat_message("assistant").write(msg["content"])
        else:
            st.chat_message("user").write(msg["content"])
    
    # Get next question
    next_question = st.session_state.controller.get_next_question()
    
    if next_question:
        # Display current question
        st.divider()
        st.info(f"**Current Question:** {next_question.question_text}")
        
        # Input for answer
        user_input = st.text_input(
            "Your answer:",
            key="answer_input",
            placeholder="Type your response here..."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 Submit Answer", type="primary"):
                if user_input:
                    # Process answer
                    result = st.session_state.controller.process_answer(
                        next_question.id, user_input
                    )
                    
                    # Add to conversation
                    st.session_state.conversation.append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    # Handle different result types
                    if result['status'] == 'success':
                        st.session_state.conversation.append({
                            "role": "agent",
                            "content": f"✓ Answer recorded. {result.get('message', '')}"
                        })
                        st.success("Answer recorded!")
                        
                    elif result['status'] == 'reask':
                        st.session_state.conversation.append({
                            "role": "agent",
                            "content": result['message']
                        })
                        st.warning("Please provide a clearer answer")
                        
                    elif result['status'] == 'invalid':
                        st.session_state.conversation.append({
                            "role": "agent",
                            "content": result['message']
                        })
                        st.warning("Invalid answer format")
                        
                    elif result['status'] == 'skipped':
                        st.session_state.conversation.append({
                            "role": "agent",
                            "content": result['message']
                        })
                        st.info("Question skipped")
                    
                    # Clear input and refresh
                    st.rerun()
        
        with col_btn2:
            if st.button("⏭️ Skip Question"):
                # Mark as skipped
                next_question.status = QuestionStatus.SKIPPED
                st.session_state.conversation.append({
                    "role": "agent",
                    "content": "I'll skip that question for now."
                })
                st.rerun()
    
    else:
        st.success("🎉 All questions completed!")
        if st.button("Show Summary"):
            progress = st.session_state.controller.get_progress()
            st.json(progress)

with col2:
    st.header("📈 Progress Tracking")
    
    # Progress visualization
    progress = st.session_state.controller.get_progress()
    
    # Donut chart
    fig = go.Figure(data=[go.Pie(
        labels=['Answered', 'Pending', 'Skipped'],
        values=[progress['answered'], progress['pending'], progress['skipped']],
        hole=.3,
        marker_colors=['#00ff00', '#ffaa00', '#ff4444']
    )])
    fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Questions table
    st.subheader("📝 Question Status")
    
    questions_data = []
    for q in st.session_state.controller.questions:
        questions_data.append({
            "ID": q.id,
            "Category": q.category,
            "Status": q.status.value,
            "Answer": q.answer[:50] + "..." if q.answer and len(q.answer) > 50 else q.answer,
            "Confidence": f"{q.answer_confidence:.0%}" if q.answer_confidence > 0 else "-"
        })
    
    df = pd.DataFrame(questions_data)
    
    # Color code status
    def color_status(val):
        if val == 'answered':
            return 'background-color: #90EE90'
        elif val == 'skipped':
            return 'background-color: #FFB6C1'
        elif val == 'reask':
            return 'background-color: #FFE4B5'
        return ''
    
    st.dataframe(
        df,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Category": st.column_config.TextColumn(width="medium"),
            "Status": st.column_config.TextColumn(width="small"),
            "Answer": st.column_config.TextColumn(width="large"),
            "Confidence": st.column_config.TextColumn(width="small")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Validation rules info
    with st.expander("📖 Validation Rules"):
        st.markdown("""
        **Numeric** (weight): Must be 50-500 lbs
        **Blood Pressure**: Format "120/80" or "120 over 80"
        **Choices**: yes/no/sometimes responses
        **Text**: Minimum 2 characters
        **Skip Logic**: Follow-up questions triggered by keywords
        **Max Attempts**: 2 attempts per question
        """)
    
    # Skip logic log
    if st.session_state.controller.skip_log:
        with st.expander("📋 Skip Logic Log"):
            for entry in st.session_state.controller.skip_log:
                st.write(f"- Question {entry['parent_question']}: {entry}")

# Footer
st.divider()
st.caption("💡 Tip: The controller automatically validates answers and handles follow-up questions")
