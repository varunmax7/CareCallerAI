# edge_case_handler.py
import re
from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

class EdgeCaseType(Enum):
    OPT_OUT = "opt_out"
    RESCHEDULE = "reschedule"
    WRONG_NUMBER = "wrong_number"
    MEDICAL_ADVICE = "medical_advice"
    EMERGENCY = "emergency"
    PRICING = "pricing"
    ESCALATION = "escalation"
    COMPLAINT = "complaint"
    TECHNICAL_ISSUE = "technical_issue"

@dataclass
class EdgeCaseResult:
    """Result from edge case handling"""
    detected: bool
    case_type: Optional[EdgeCaseType]
    confidence: float
    response: str
    action: str  # "end_call", "escalate", "continue", "transfer", "capture_info"
    extracted_data: Optional[Dict]
    needs_human: bool = False

class EdgeCaseHandler:
    def __init__(self):
        """Initialize edge case handler with patterns and responses"""
        
        # Define patterns for each edge case
        self.patterns = {
            EdgeCaseType.OPT_OUT: {
                "patterns": [
                    r"\b(opt out|opt-out|stop calling|don'?t want|not interested|remove me|do not call|unsubscribe|quit|end call)\b",
                    r"\b(no thanks|no thank you|not now|maybe later|another time)\b",
                    r"\b(cancel|stop|leave me alone|don'?t call)\b"
                ],
                "confidence": 0.85,
                "action": "end_call"
            },
            
            EdgeCaseType.RESCHEDULE: {
                "patterns": [
                    r"\b(reschedule|call back|called back|different time|better time)\b",
                    r"\b(not a good time|busy now|can'?t talk|in a meeting|working)\b",
                    r"\b(call (tomorrow|next week|later|this evening|morning))\b",
                    r"\b(available (at|on)|\bavailable\b)"
                ],
                "confidence": 0.8,
                "action": "capture_info"
            },
            
            EdgeCaseType.WRONG_NUMBER: {
                "patterns": [
                    r"\b(wrong number|incorrect number|not (him|her|them)|no one by that name)\b",
                    r"\b(you have the wrong|not this person|don'?t know who that is)\b",
                    r"\b(who is this|why are you calling)\b"
                ],
                "confidence": 0.9,
                "action": "end_call"
            },
            
            EdgeCaseType.MEDICAL_ADVICE: {
                "patterns": [
                    r"\b(should I take|can I take|is it safe|what dosage|how often)\b",
                    r"\b(what (should|can) I do about|how to treat|recommend|suggest)\b",
                    r"\b(is this normal|should I worry|am I okay|is it serious)\b",
                    r"\b(can you prescribe|do I need|will it help)\b"
                ],
                "confidence": 0.85,
                "action": "safe_response"
            },
            
            EdgeCaseType.EMERGENCY: {
                "patterns": [
                    r"\b(chest pain|heart attack|stroke|can'?t breathe|severe bleeding)\b",
                    r"\b(emergency|911|ambulance|hospital now|medical emergency)\b",
                    r"\b(passing out|unconscious|seizure|choking|suicidal)\b",
                    r"\b(bleeding (heavily|profusely)|difficulty breathing|shortness of breath)\b"
                ],
                "confidence": 0.95,
                "action": "escalate_immediate"
            },
            
            EdgeCaseType.PRICING: {
                "patterns": [
                    r"\b(how much|price|cost|expensive|afford|insurance cover|co-pay|copay)\b",
                    r"\b(what'?s the price|how much (will|does) it cost|cost of medication)\b",
                    r"\b(covered by insurance|insurance pay|out of pocket)\b"
                ],
                "confidence": 0.85,
                "action": "transfer"
            },
            
            EdgeCaseType.COMPLAINT: {
                "patterns": [
                    r"\b(complaint|unhappy|not satisfied|bad service|frustrated|angry)\b",
                    r"\b(never (received|got)|late|delayed|missed)\b",
                    r"\b(speak to (manager|supervisor)|escalate|higher up)\b"
                ],
                "confidence": 0.75,
                "action": "escalate"
            },
            
            EdgeCaseType.TECHNICAL_ISSUE: {
                "patterns": [
                    r"\b(can'?t hear|breaking up|connection issue|call dropped)\b",
                    r"\b(not working|error|problem with|technical issue)\b",
                    r"\b(speak (slower|louder|clearly)|repeat|what did you say)\b"
                ],
                "confidence": 0.7,
                "action": "continue"
            }
        }
        
        # Response templates
        self.responses = {
            EdgeCaseType.OPT_OUT: [
                "I understand you'd prefer not to continue. I'll note that in your record. Have a good day!",
                "No problem at all. I'll make sure you don't receive further calls. Take care!",
                "Thank you for letting me know. I'll update your preferences. Goodbye!"
            ],
            
            EdgeCaseType.RESCHEDULE: [
                "I can help with that. What day and time would work better for you?",
                "Of course. When should we call you back? Please provide a date and time.",
                "I understand. Let me find a better time. When are you available?"
            ],
            
            EdgeCaseType.WRONG_NUMBER: [
                "I apologize for the mistake. I'll remove this number from our records. Have a good day!",
                "Sorry to bother you. I'll update our system. Goodbye!",
                "My apologies for the wrong number. I'll correct this immediately. Take care!"
            ],
            
            EdgeCaseType.MEDICAL_ADVICE: [
                "I'm not able to provide medical advice. Please speak with your doctor about this.",
                "That's a question for your healthcare provider. I recommend consulting your doctor.",
                "For your safety, I can't give medical advice. Your doctor is the best person to help with this."
            ],
            
            EdgeCaseType.EMERGENCY: [
                "This sounds serious. I'm going to connect you with a human operator immediately. Please stay on the line.",
                "I hear your concern. I'm escalating this to emergency services right now. Please hold.",
                "For your safety, I'm transferring you to our emergency response team. Please don't hang up."
            ],
            
            EdgeCaseType.PRICING: [
                "For pricing details, I'll need to transfer you to our billing department. One moment please.",
                "I understand you're asking about cost. Let me connect you with someone who can help with pricing.",
                "Price-related questions are handled by our pharmacy team. I'll transfer you now."
            ],
            
            EdgeCaseType.COMPLAINT: [
                "I hear your frustration. Let me connect you with a supervisor who can better assist you.",
                "I understand you're not satisfied. I'll escalate this to a human agent right away.",
                "Thank you for sharing your concern. Let me transfer you to someone who can help resolve this."
            ],
            
            EdgeCaseType.TECHNICAL_ISSUE: [
                "I apologize for the connection issue. Let me speak more clearly. Did you catch that?",
                "I'm sorry you're having trouble hearing me. Let me repeat that more slowly.",
                "Let me try that again to make sure you heard clearly."
            ]
        }
        
        # Time parsing patterns for rescheduling
        self.time_patterns = {
            "time_of_day": r"\b(tomorrow|today|tonight|morning|afternoon|evening|night)\b",
            "day_of_week": r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            "specific_time": r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
            "relative_time": r"\b(later|soon|in (\d+) (hours?|minutes?|days?))\b"
        }
        
        # Escalation triggers
        self.escalation_keywords = {
            "emergency": ["chest pain", "heart attack", "stroke", "can't breathe", "severe bleeding"],
            "complaint": ["manager", "supervisor", "complain", "unhappy", "angry", "frustrated"],
            "medical": ["doctor", "prescription", "dosage", "side effect severe"]
        }
        
        # Track detected edge cases for this call
        self.detected_cases = []
        self.escalation_required = False
        self.escalation_reason = None
    
    def detect_edge_case(self, text: str) -> Optional[EdgeCaseResult]:
        """Detect if text contains an edge case"""
        text_lower = text.lower()
        
        # Check each pattern type
        for case_type, config in self.patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    confidence = config["confidence"]
                    
                    # Adjust confidence based on match strength
                    match = re.search(pattern, text_lower, re.IGNORECASE)
                    if match:
                        match_length = len(match.group(0))
                        if match_length > 10:
                            confidence = min(1.0, confidence + 0.1)
                    
                    # Generate appropriate response
                    response = self._get_response(case_type)
                    
                    # Extract data if needed
                    extracted_data = self._extract_data(case_type, text)
                    
                    # Log detection
                    self.detected_cases.append({
                        "type": case_type.value,
                        "text": text,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Check if escalation needed
                    needs_human = case_type in [EdgeCaseType.EMERGENCY, EdgeCaseType.COMPLAINT]
                    if needs_human:
                        self.escalation_required = True
                        self.escalation_reason = case_type.value
                    
                    return EdgeCaseResult(
                        detected=True,
                        case_type=case_type,
                        confidence=confidence,
                        response=response,
                        action=config["action"],
                        extracted_data=extracted_data,
                        needs_human=needs_human
                    )
        
        return None
    
    def _get_response(self, case_type: EdgeCaseType) -> str:
        """Get appropriate response for edge case"""
        import random
        responses = self.responses.get(case_type, ["I understand. Let me help you with that."])
        return random.choice(responses)
    
    def _extract_data(self, case_type: EdgeCaseType, text: str) -> Optional[Dict]:
        """Extract relevant data from edge case text"""
        extracted = {}
        
        if case_type == EdgeCaseType.RESCHEDULE:
            # Extract date/time information
            text_lower = text.lower()
            
            # Extract day
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                if day in text_lower:
                    extracted["day"] = day
                    break
            
            # Extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                ampm = time_match.group(3) or ""
                extracted["time"] = f"{hour}:{minute:02d} {ampm}".strip()
            
            # Extract relative time
            if "tomorrow" in text_lower:
                extracted["relative"] = "tomorrow"
            elif "later" in text_lower:
                extracted["relative"] = "later"
            
        elif case_type == EdgeCaseType.PRICING:
            # Extract medication name if mentioned
            words = text.split()
            for word in words:
                if word not in ["how", "much", "price", "cost", "does", "what"]:
                    if len(word) > 3:
                        extracted["medication_mentioned"] = word
        
        elif case_type == EdgeCaseType.EMERGENCY:
            # Extract emergency type
            for emergency_type in ["chest pain", "heart attack", "stroke", "breathing"]:
                if emergency_type in text_lower:
                    extracted["emergency_type"] = emergency_type
                    break
            extracted["severity"] = "high"
        
        return extracted if extracted else None
    
    def handle_reschedule(self, text: str) -> Dict:
        """Handle reschedule request with time capture"""
        extracted = self._extract_data(EdgeCaseType.RESCHEDULE, text)
        
        if extracted:
            if "day" in extracted and "time" in extracted:
                return {
                    "status": "success",
                    "message": f"I'll schedule a call for {extracted.get('day', '')} at {extracted.get('time', '')}. Is that correct?",
                    "scheduled_time": extracted,
                    "needs_confirmation": True
                }
            elif "relative" in extracted:
                return {
                    "status": "pending",
                    "message": f"I'll have someone call you {extracted['relative']}. Is there a specific time that works best?",
                    "scheduled_time": extracted,
                    "needs_more_info": True
                }
        
        return {
            "status": "needs_info",
            "message": "I'd be happy to reschedule. What day and time works best for you?",
            "needs_more_info": True
        }
    
    def handle_medical_advice(self, text: str) -> Dict:
        """Handle medical advice requests safely"""
        return {
            "status": "redirected",
            "message": "I'm not able to provide medical advice. Would you like me to note this question for your doctor?",
            "action": "note_for_doctor",
            "user_question": text
        }
    
    def handle_emergency(self, text: str) -> Dict:
        """Handle emergency with immediate escalation"""
        extracted = self._extract_data(EdgeCaseType.EMERGENCY, text)
        
        return {
            "status": "escalated",
            "message": "I'm connecting you with emergency services. Please stay on the line.",
            "escalation_level": "critical",
            "emergency_details": extracted,
            "action": "call_911" if "chest pain" in text.lower() or "can't breathe" in text.lower() else "escalate_to_human"
        }
    
    def handle_pricing(self, text: str) -> Dict:
        """Handle pricing questions with transfer"""
        extracted = self._extract_data(EdgeCaseType.PRICING, text)
        
        return {
            "status": "transfer",
            "message": "I'll transfer you to our billing department. One moment please.",
            "transfer_to": "billing",
            "context": extracted
        }
    
    def handle_opt_out(self, text: str) -> Dict:
        """Handle opt-out with grace"""
        return {
            "status": "opted_out",
            "message": "I understand. I'll update your preferences so you won't receive further calls. Have a good day!",
            "action": "update_preferences",
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_wrong_number(self, text: str) -> Dict:
        """Handle wrong number situation"""
        return {
            "status": "wrong_number",
            "message": "I apologize for the mistake. I'll remove this number from our records. Goodbye!",
            "action": "remove_number",
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_complaint(self, text: str) -> Dict:
        """Handle complaints with escalation"""
        return {
            "status": "escalated",
            "message": "I hear your concern. Let me connect you with a supervisor who can better assist you.",
            "escalation_level": "supervisor",
            "complaint": text,
            "action": "transfer_to_human"
        }
    
    def should_escalate(self) -> Tuple[bool, Optional[str]]:
        """Check if call should be escalated"""
        return self.escalation_required, self.escalation_reason
    
    def get_edge_case_summary(self) -> Dict:
        """Get summary of all detected edge cases"""
        return {
            "total_detected": len(self.detected_cases),
            "cases": self.detected_cases,
            "escalation_needed": self.escalation_required,
            "escalation_reason": self.escalation_reason
        }
    
    def reset(self):
        """Reset for new call"""
        self.detected_cases = []
        self.escalation_required = False
        self.escalation_reason = None
    
    def get_priority(self, case_type: EdgeCaseType) -> int:
        """Get priority level for edge case (higher = more urgent)"""
        priorities = {
            EdgeCaseType.EMERGENCY: 100,
            EdgeCaseType.MEDICAL_ADVICE: 80,
            EdgeCaseType.COMPLAINT: 70,
            EdgeCaseType.PRICING: 50,
            EdgeCaseType.RESCHEDULE: 40,
            EdgeCaseType.OPT_OUT: 30,
            EdgeCaseType.WRONG_NUMBER: 30,
            EdgeCaseType.TECHNICAL_ISSUE: 20
        }
        return priorities.get(case_type, 50)
    
    def validate_response_safety(self, response: str) -> bool:
        """Validate that response doesn't contain prohibited content"""
        prohibited = [
            "medical advice",
            "should take",
            "recommend",
            "prescribe",
            "diagnose"
        ]
        
        response_lower = response.lower()
        for prohibited_word in prohibited:
            if prohibited_word in response_lower:
                return False
        return True
