# agent_core.py
from openai import OpenAI
import json
from typing import Dict, List, Optional
from datetime import datetime
from question_controller import QuestionFlowController
from context_memory import ContextMemory
from edge_case_handler import EdgeCaseHandler
from response_storage import ResponseStorage, AnswerConfidence
from validation_system import ValidationSystem

class VoiceAgent:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the AI Voice Agent"""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Add question controller
        self.question_controller = QuestionFlowController()
        
        # Add context memory
        self.context_memory = ContextMemory()
        
        # Add edge case handler
        self.edge_handler = EdgeCaseHandler()
        
        # Call state
        self.call_active = True
        self.conversation_history = []
        self.current_question_index = 0
        
        # Define the 14 health questions
        self.questions = [
            {"id": 1, "category": "weight", "question": "Have you checked your weight recently?", "answer": None},
            {"id": 2, "category": "side_effects", "question": "Have you experienced any side effects from your medication?", "answer": None},
            {"id": 3, "category": "allergies", "question": "Have you had any allergic reactions to medications?", "answer": None},
            {"id": 4, "category": "medication_taken", "question": "Are you taking your medication as prescribed?", "answer": None},
            {"id": 5, "category": "new_medications", "question": "Have you started any new medications since your last refill?", "answer": None},
            {"id": 6, "category": "hospitalization", "question": "Have you been hospitalized since your last refill?", "answer": None},
            {"id": 7, "category": "doctor_visit", "question": "Have you seen your doctor recently?", "answer": None},
            {"id": 8, "category": "blood_pressure", "question": "Have you checked your blood pressure?", "answer": None},
            {"id": 9, "category": "symptoms", "question": "Are you experiencing any new symptoms?", "answer": None},
            {"id": 10, "category": "refill_timing", "question": "Do you need a refill now?", "answer": None},
            {"id": 11, "category": "medication_effectiveness", "question": "Is your medication working well for you?", "answer": None},
            {"id": 12, "category": "appetite", "question": "Have you noticed any changes in your appetite?", "answer": None},
            {"id": 13, "category": "sleep", "question": "How has your sleep been lately?", "answer": None},
            {"id": 14, "category": "concerns", "question": "Do you have any other concerns about your health or medication?", "answer": None}
        ]
        
        # Patient info
        self.patient_info = {
            "name": "Mr. Johnson",  # Simulation default
            "confirmed_identity": False,
            "call_outcome": None,
            "escalation_reason": None
        }
        
        # Add response storage
        self.storage = ResponseStorage()
        
        # Add validation system
        self.validator = ValidationSystem()
        
        # Structured responses (matches training data format)
        self.responses_json = []
        
    def get_system_prompt(self) -> str:
        """Define the agent's role and behavior"""
        return """You are an AI healthcare assistant calling to check on a patient's medication refill.

**YOUR ROLE:**
- Be friendly, professional, and empathetic
- Speak clearly and naturally
- Never give medical advice - always say "please consult your doctor"
- Escalate to human if patient has severe symptoms or emergencies

**YOUR TASKS:**
1. Greet patient and confirm identity
2. Ask health questions naturally (don't sound robotic)
3. Handle off-script questions about pricing, dosage, side effects
4. Detect when to escalate (emergency, severe symptoms, confusion)
5. Handle edge cases: opt-out, reschedule, wrong number

**RESPONSE RULES:**
- Keep responses brief and conversational (1-2 sentences max)
- If patient asks for medical advice: "I'm not able to provide medical advice. Please speak with your doctor about this."
- If patient wants to opt out: "I understand. I'll note that you'd prefer not to continue. Have a good day!"
- If patient wants to reschedule: "I can help with that. When would be a better time to call back?"
- If emergency (chest pain, severe bleeding, etc.): "This sounds serious. I'm going to connect you with a human operator immediately."

**FORMAT:**
Return your response as JSON with these fields:
{
    "agent_message": "your spoken response here",
    "action": "continue" or "escalate" or "end_call",
    "extracted_answer": {
        "question_id": 1,
        "answer": "patient's answer if detected",
        "confidence": 0.0-1.0
    },
    "off_script_detected": true/false,
    "escalation_reason": "reason if escalating",
    "call_status": "active/opt_out/reschedule/completed"
}
"""
    
    def get_asked_questions_summary(self) -> str:
        """Get summary of which questions have been asked"""
        asked = [q for q in self.questions if q["answer"] is not None]
        remaining = [q for q in self.questions if q["answer"] is None]
        
        if asked:
            summary = "Questions already asked and answered:\n"
            for q in asked:
                summary += f"- {q['question']}: {q['answer']}\n"
        else:
            summary = "No questions asked yet.\n"
            
        if remaining:
            summary += f"\nNext question to ask: {remaining[0]['question']}"
            
        return summary
    
    def _generate_llm_response(self, system_prompt: str, user_text: str) -> Optional[Dict]:
        """Generate a natural response using OpenAI LLM"""
        if not self.client.api_key or self.client.api_key == "sk-your-actual-key-here":
            return None
            
        try:
            # Prepare context for LLM
            context = self.context_memory.get_context_for_llm()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"CURRENT CONTEXT:\n{context}"},
                {"role": "user", "content": user_text}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

    def process_user_input(self, user_text: str) -> Dict:
        """Process user input with edge case handling and LLM-powered responses"""
        
        # 1. Handle starting the call (empty input)
        if not user_text:
            greeting = f"Hello! This is CareCaller calling for {self.patient_info['name']}. Am I speaking with the patient?"
            self.context_memory.add_message("agent", greeting)
            return {
                "agent_message": greeting,
                "action": "continue",
                "call_status": "waiting_identity"
            }

        # 2. Add patient message to context and storage
        self.context_memory.add_message("patient", user_text)
        self.storage.add_conversation_turn("patient", user_text)
        
        # 3. Check for edge cases first (highest priority)
        edge_result = self.edge_handler.detect_edge_case(user_text)
        if edge_result:
            self.context_memory.add_message("agent", edge_result.response)
            self.storage.add_conversation_turn("agent", edge_result.response)
            if edge_result.action in ["end_call", "escalate_immediate"]:
                self.call_active = False
                self.patient_info["call_outcome"] = edge_result.case_type.value
                self.storage.end_time = datetime.now()
            
            return {
                "agent_message": edge_result.response,
                "action": edge_result.action,
                "edge_case": edge_result.case_type.value
            }

        # 4. Handle Identity Confirmation phase
        if not self.patient_info["confirmed_identity"]:
            user_text_lower = user_text.lower()
            
            # Simple "Yes" detection
            if any(word in user_text_lower for word in ["yes", "speaking", "correct", "this is him", "this is her"]):
                self.patient_info["confirmed_identity"] = True
                self.context_memory.patient_profile.confirmed = True  # Sync with profile
                first_q = self.question_controller.get_next_question(mark_as_asked=True)
                if first_q:
                    agent_response = f"Great, thank you. I'm calling to do a quick health check-in. {first_q.question_text}"
                else:
                    agent_response = "Great, thank you. I see we have everything up to date already. How are you feeling today?"
                
                self.context_memory.add_message("agent", agent_response)
                self.storage.add_conversation_turn("agent", agent_response)
                return {
                    "agent_message": agent_response,
                    "action": "continue",
                    "call_status": "identity_confirmed"
                }
            
            # Flexible detection using LLM for "Not the person" or "I am [Name]"
            llm_id_check = self._generate_llm_response(
                "Verify if this person is our patient or someone else. " +
                f"Patient name: {self.patient_info['name']}. " +
                "Return JSON: {\"is_correct_person\": bool, \"is_wrong_person\": bool, \"new_name_detected\": string or null}",
                f"User said: {user_text}"
            )
            
            if llm_id_check:
                if llm_id_check.get("is_correct_person"):
                    self.patient_info["confirmed_identity"] = True
                    self.context_memory.patient_profile.confirmed = True  # Sync with profile
                    first_q = self.question_controller.get_next_question(mark_as_asked=True)
                    if first_q:
                        agent_response = f"Thank you for confirming. I'm calling for a health check-in. {first_q.question_text}"
                    else:
                        agent_response = "Thank you for confirming. Let's get started with your check-in."
                elif llm_id_check.get("is_wrong_person"):
                        detected_name = llm_id_check.get("new_name_detected", "someone else")
                        agent_response = f"Oh, I'm sorry. I was looking for {self.patient_info['name']}. Is {self.patient_info['name']} available to talk?"
                else:
                    agent_response = f"I'm sorry, I need to speak with {self.patient_info['name']}. Am I speaking with {self.patient_info['name']}?"
            else:
                agent_response = f"I'm sorry, I didn't quite catch that. Is this {self.patient_info['name']}?"
                
            self.context_memory.add_message("agent", agent_response)
            self.storage.add_conversation_turn("agent", agent_response)
            return {
                "agent_message": agent_response,
                "action": "continue",
                "call_status": "waiting_identity"
            }

        # 5. Handle Question Flow
        active_question = self.question_controller.get_active_question()
        
        if active_question:
            # Process answer
            validation_result = self.question_controller.process_answer(
                active_question.id, user_text
            )
            
            # Optimization: Skip LLM for simple validated numeric/choice answers to save time
            is_simple_answer = len(user_text.split()) <= 3 and validation_result['status'] == 'success'
            
            llm_response = None
            if not is_simple_answer:
                llm_response = self._generate_llm_response(self.get_system_prompt(), user_text)
            
            if llm_response and "agent_message" in llm_response:
                agent_response = llm_response["agent_message"]
                # Still use controller to move state
                if validation_result['status'] == 'success':
                    next_q = self.question_controller.get_next_question(mark_as_asked=True)
                    if next_q:
                        # Continue conversation
                        pass
                    else:
                        agent_response = "I've completed all the questions. Thank you for your time. Have a wonderful day!"
                        self.call_active = False
                    self.storage.add_answer(
                        question_id=active_question.id,
                        answer=user_text,
                        confidence=AnswerConfidence.HIGH,  # LLM extracted
                        confidence_score=0.9
                    )
                
                self.storage.add_conversation_turn("agent", agent_response)
                return {
                    "agent_message": agent_response,
                    "action": llm_response.get("action", "continue"),
                    "progress": self.question_controller.get_progress()
                }
            
            # Fallback to Rule-based responses for question flow
            if validation_result['status'] == 'success':
                # Sync with storage
                self.storage.add_answer(
                    question_id=active_question.id,
                    answer=user_text,
                    confidence=AnswerConfidence.HIGH,
                    confidence_score=0.9,
                    source="direct"
                )
                
                next_q = self.question_controller.get_next_question(mark_as_asked=True)
                if next_q:
                    agent_response = f"Thank you. {next_q.question_text}"
                else:
                    agent_response = "I've completed all the questions. Thank you for your time. Have a wonderful day!"
                    self.call_active = False
                    self.storage.end_time = datetime.now()
            else:
                agent_response = validation_result.get('message', "I understand. Let's move on.")
                
            self.context_memory.add_message("agent", agent_response)
            self.storage.add_conversation_turn("agent", agent_response)
            return {
                "agent_message": agent_response,
                "action": "continue" if self.call_active else "end_call",
                "progress": self.question_controller.get_progress()
            }
        
        # 6. Default response if something went wrong or call is finishing
        completion_msg = "Thank you for your cooperation. Goodbye!"
        self.call_active = False
        self.storage.end_time = datetime.now()
        self.storage.add_conversation_turn("agent", completion_msg)
        return {"agent_message": completion_msg, "action": "end_call"}
    
    def get_full_context(self) -> Dict:
        """Get full context for debugging/export"""
        return self.context_memory.to_dict()
    
    def check_edge_cases(self, user_text: str) -> Optional[Dict]:
        """Quick rule-based check for common edge cases"""
        text_lower = user_text.lower()
        
        # Emergency keywords
        emergencies = ["chest pain", "heart attack", "stroke", "severe bleeding", 
                      "can't breathe", "suicide", "emergency"]
        for emergency in emergencies:
            if emergency in text_lower:
                return {
                    "agent_message": "This sounds serious. I'm going to connect you with a human operator immediately. Please hold.",
                    "action": "escalate",
                    "escalation_reason": f"Emergency detected: {emergency}",
                    "call_status": "escalated"
                }
        
        # Opt-out patterns
        opt_out_phrases = ["don't want to continue", "stop calling", "opt out", 
                          "not interested", "remove me", "do not call"]
        for phrase in opt_out_phrases:
            if phrase in text_lower:
                return {
                    "agent_message": "I understand you'd prefer not to continue. I'll note that in your record. Have a good day!",
                    "action": "end_call",
                    "call_status": "opted_out"
                }
        
        # Reschedule patterns
        reschedule_phrases = ["reschedule", "call back later", "different time", 
                             "not a good time", "busy now"]
        for phrase in reschedule_phrases:
            if phrase in text_lower:
                return {
                    "agent_message": "I can help with that. When would be a better time for us to call back? Please let me know a date and time.",
                    "action": "continue",
                    "call_status": "reschedule_requested"
                }
        
        # Wrong number
        if "wrong number" in text_lower or "not this person" in text_lower:
            return {
                "agent_message": "I apologize for the mistake. I'll remove this number from our records. Have a good day!",
                "action": "end_call",
                "call_status": "wrong_number"
            }
        
        return None
    
    def store_answer(self, question_id: int, answer: str, confidence: float):
        """Store answer in structured format"""
        if question_id and answer:
            question = self.questions[question_id - 1]
            question["answer"] = answer
            
            # Add to structured responses
            self.responses_json.append({
                "question": question["question"],
                "category": question["category"],
                "answer": answer,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_completion_status(self) -> Dict:
        """Get call completion status"""
        answered = [q for q in self.questions if q["answer"] is not None]
        return {
            "total_questions": len(self.questions),
            "answered": len(answered),
            "completion_rate": len(answered) / len(self.questions),
            "missing_categories": [q["category"] for q in self.questions if q["answer"] is None]
        }
    
    def get_structured_output(self) -> Dict:
        """Get final structured output matching training data"""
        # Ensure profile is fully synced with agent identity state before reporting
        self.context_memory.patient_profile.confirmed = self.patient_info.get("confirmed_identity", False)
        if self.patient_info.get("name"):
            self.context_memory.patient_profile.name = self.patient_info["name"]
            
        output = self.storage.to_json()
        # Add profile info for the summary
        output['patient_profile'] = self.context_memory.patient_profile.to_dict()
        output['patient_info'] = self.patient_info
        return output
    
    def reset(self, patient_name: str = "Mr. Johnson"):
        """Reset agent for new call"""
        self.call_active = True
        self.conversation_history = []
        self.current_question_index = 0
        
        # Reset questions in agent list
        for q in self.questions:
            q["answer"] = None
        
        # Reset the controller and other components
        self.question_controller.reset()
        self.context_memory.reset()
        self.edge_handler.reset()
        self.storage.reset()
        
        self.patient_info = {
            "name": patient_name,
            "confirmed_identity": False,
            "call_outcome": None,
            "escalation_reason": None
        }
        self.responses_json = []
