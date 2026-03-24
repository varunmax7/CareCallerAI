# question_controller.py
import re
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json

class QuestionStatus(Enum):
    PENDING = "pending"
    ASKED = "asked"
    ANSWERED = "answered"
    SKIPPED = "skipped"
    REASK = "reask"

class AnswerValidation(Enum):
    VALID = "valid"
    INVALID = "invalid"
    UNCLEAR = "unclear"
    NEEDS_FOLLOWUP = "needs_followup"

@dataclass
class Question:
    """Individual question structure"""
    id: int
    category: str
    question_text: str
    follow_up: Optional[str] = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    conditional: Optional[Dict] = None  # e.g., {"if_answer": "yes", "then_ask": follow_up}
    status: QuestionStatus = QuestionStatus.PENDING
    answer: Optional[str] = None
    answer_confidence: float = 0.0
    validation_notes: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 2

class QuestionFlowController:
    def __init__(self):
        """Initialize the question flow controller"""
        self.questions = self._define_questions()
        self.current_question_index = 0
        self.question_queue = []
        self.completed_categories = set()
        self.skip_log = []
        
    def _define_questions(self) -> List[Question]:
        """Define all 14 questions with validation rules and skip logic"""
        
        questions = [
            # 1. Weight
            Question(
                id=1, category="weight",
                question_text="Have you checked your weight recently?",
                follow_up="What was your weight in pounds?",
                validation_rules={
                    "type": "numeric",
                    "range": [50, 500],
                    "units": "pounds",
                    "required": True
                }
            ),
            
            # 2. Side Effects
            Question(
                id=2, category="side_effects",
                question_text="Have you experienced any side effects from your medication?",
                follow_up="Can you describe the side effects you're experiencing?",
                validation_rules={
                    "type": "text",
                    "required": True,
                    "min_length": 2
                },
                conditional={
                    "if_answer_contains": ["yes", "yeah", "yep", "sometimes", "occasionally"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 3. Allergies
            Question(
                id=3, category="allergies",
                question_text="Have you had any allergic reactions to medications?",
                follow_up="What medications are you allergic to?",
                validation_rules={
                    "type": "text",
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["yes", "yeah", "yep", "reaction"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 4. Medication Adherence
            Question(
                id=4, category="medication_taken",
                question_text="Are you taking your medication as prescribed?",
                follow_up="How many doses have you missed in the past week?",
                validation_rules={
                    "type": "choice",
                    "options": ["yes", "no", "sometimes", "always", "never"],
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["no", "sometimes", "not", "missed"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 5. New Medications
            Question(
                id=5, category="new_medications",
                question_text="Have you started any new medications since your last refill?",
                follow_up="What medications did you start and why?",
                validation_rules={
                    "type": "text",
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["yes", "started", "new", "prescribed"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 6. Hospitalization
            Question(
                id=6, category="hospitalization",
                question_text="Have you been hospitalized since your last refill?",
                follow_up="What was the reason for hospitalization?",
                validation_rules={
                    "type": "text",
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["yes", "hospital", "admitted", "emergency"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 7. Doctor Visit
            Question(
                id=7, category="doctor_visit",
                question_text="Have you seen your doctor recently?",
                follow_up="What did your doctor say about your progress?",
                validation_rules={
                    "type": "text",
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["yes", "saw", "visited", "appointment"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 8. Blood Pressure
            Question(
                id=8, category="blood_pressure",
                question_text="Have you checked your blood pressure?",
                follow_up="What were your blood pressure readings?",
                validation_rules={
                    "type": "blood_pressure",
                    "format": "systolic/diastolic",
                    "range": {"systolic": [90, 200], "diastolic": [60, 120]},
                    "required": False
                }
            ),
            
            # 9. New Symptoms
            Question(
                id=9, category="symptoms",
                question_text="Are you experiencing any new symptoms?",
                follow_up="What symptoms are you having?",
                validation_rules={
                    "type": "text",
                    "required": True,
                    "min_length": 2
                },
                conditional={
                    "if_answer_contains": ["yes", "new", "feeling", "experiencing"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 10. Refill Timing
            Question(
                id=10, category="refill_timing",
                question_text="Do you need a refill now?",
                follow_up="When would you like to schedule your refill?",
                validation_rules={
                    "type": "choice",
                    "options": ["yes", "no", "soon", "later", "emergency"],
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["yes", "soon", "need"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 11. Medication Effectiveness
            Question(
                id=11, category="medication_effectiveness",
                question_text="Is your medication working well for you?",
                follow_up="Can you tell me more about how it's working?",
                validation_rules={
                    "type": "choice",
                    "options": ["yes", "no", "somewhat", "not sure"],
                    "required": True
                },
                conditional={
                    "if_answer_contains": ["no", "not", "somewhat"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 12. Appetite
            Question(
                id=12, category="appetite",
                question_text="Have you noticed any changes in your appetite?",
                follow_up="How has your appetite changed?",
                validation_rules={
                    "type": "text",
                    "required": False
                },
                conditional={
                    "if_answer_contains": ["yes", "change", "different", "less", "more"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 13. Sleep
            Question(
                id=13, category="sleep",
                question_text="How has your sleep been lately?",
                follow_up="Can you describe your sleep patterns?",
                validation_rules={
                    "type": "text",
                    "required": False,
                    "min_length": 2
                },
                conditional={
                    "if_answer_contains": ["poor", "bad", "difficulty", "trouble", "not well"],
                    "then_ask": "follow_up"
                }
            ),
            
            # 14. General Concerns
            Question(
                id=14, category="concerns",
                question_text="Do you have any other concerns about your health or medication?",
                follow_up=None,
                validation_rules={
                    "type": "text",
                    "required": False
                }
            )
        ]
        
        return questions
    
    def validate_answer(self, question: Question, answer: str) -> tuple[AnswerValidation, str, Optional[Dict]]:
        """Validate answer against question's validation rules"""
        
        if not answer or not answer.strip():
            return AnswerValidation.INVALID, "I didn't catch that. Could you please answer?", None
        
        answer_lower = answer.lower().strip()
        rules = question.validation_rules
        validation_type = rules.get("type", "text")
        
        # Numeric validation
        if validation_type == "numeric":
            try:
                # Extract numbers from text
                numbers = re.findall(r'\d+', answer)
                if not numbers:
                    return AnswerValidation.INVALID, "I need a number for that. What is your weight in pounds?", None
                
                value = float(numbers[0])
                range_min, range_max = rules.get("range", [0, 1000])
                
                if value < range_min:
                    return AnswerValidation.INVALID, f"Are you sure? That seems low. Could you confirm your {question.category}?", None
                elif value > range_max:
                    return AnswerValidation.INVALID, f"That seems high. Could you double-check your {question.category}?", None
                else:
                    return AnswerValidation.VALID, "OK", {"value": value, "units": rules.get("units")}
                    
            except:
                return AnswerValidation.INVALID, "I didn't understand the number. Could you repeat that?", None
        
        # Blood pressure validation
        elif validation_type == "blood_pressure":
            # Match patterns like "120/80", "120 over 80"
            pattern = r'(\d{2,3})\s*[/over]+\s*(\d{2,3})'
            match = re.search(pattern, answer_lower)
            
            if match:
                systolic = int(match.group(1))
                diastolic = int(match.group(2))
                range_sys = rules.get("range", {}).get("systolic", [90, 200])
                range_dia = rules.get("range", {}).get("diastolic", [60, 120])
                
                if range_sys[0] <= systolic <= range_sys[1] and range_dia[0] <= diastolic <= range_dia[1]:
                    return AnswerValidation.VALID, "OK", {"systolic": systolic, "diastolic": diastolic}
                else:
                    return AnswerValidation.INVALID, "Those readings seem unusual. Could you confirm them with your doctor?", None
            else:
                return AnswerValidation.UNCLEAR, "I didn't catch the numbers. What were your blood pressure readings?", None
        
        # Choice validation
        elif validation_type == "choice":
            options = rules.get("options", [])
            for option in options:
                if option in answer_lower:
                    return AnswerValidation.VALID, "OK", {"choice": option}
            
            # If no match but answer is valid text
            if len(answer) > 3:
                return AnswerValidation.VALID, "OK", {"answer": answer}
            else:
                return AnswerValidation.UNCLEAR, f"Could you say yes or no? {question.question_text}", None
        
        # Text validation
        else:
            min_length = rules.get("min_length", 1)
            if len(answer) >= min_length:
                # Check if answer is clear enough
                unclear_patterns = ["i don't know", "not sure", "maybe", "i guess", "um", "uh"]
                if any(pattern in answer_lower for pattern in unclear_patterns):
                    return AnswerValidation.UNCLEAR, "I want to make sure I understand correctly. Could you tell me more?", None
                return AnswerValidation.VALID, "OK", {"answer": answer}
            else:
                return AnswerValidation.UNCLEAR, "Could you provide a bit more detail?", None
    
    def process_answer(self, question_id: int, answer: str) -> Dict:
        """Process and validate an answer for a question"""
        
        question = self.get_question(question_id)
        if not question:
            return {"error": "Question not found"}
        
        # Validate answer
        validation_status, message, parsed_data = self.validate_answer(question, answer)
        
        # Handle validation results
        if validation_status == AnswerValidation.VALID:
            question.answer = answer
            question.answer_confidence = 1.0
            question.status = QuestionStatus.ANSWERED
            question.validation_notes = "Valid answer"
            self.completed_categories.add(question.category)
            
            # Check if we need to add follow-up to queue
            self._handle_follow_up(question, answer, parsed_data)
            
            return {
                "status": "success",
                "message": "Answer recorded",
                "question_id": question_id,
                "answer": answer,
                "parsed_data": parsed_data,
                "next_question": self.get_next_question()
            }
            
        elif validation_status == AnswerValidation.UNCLEAR:
            question.attempts += 1
            
            if question.attempts >= question.max_attempts:
                # Mark as answered with low confidence and move on
                question.answer = answer
                question.answer_confidence = 0.3
                question.status = QuestionStatus.ANSWERED
                question.validation_notes = f"Unclear after {question.attempts} attempts"
                self.completed_categories.add(question.category)
                
                return {
                    "status": "partial",
                    "message": "I'll note that down. Let's move on.",
                    "question_id": question_id,
                    "answer": answer,
                    "confidence": 0.3,
                    "next_question": self.get_next_question()
                }
            else:
                question.status = QuestionStatus.REASK
                return {
                    "status": "reask",
                    "message": message,
                    "question_id": question_id,
                    "attempts": question.attempts,
                    "max_attempts": question.max_attempts
                }
        
        else:  # INVALID
            question.attempts += 1
            
            if question.attempts >= question.max_attempts:
                # Skip question after max attempts
                question.status = QuestionStatus.SKIPPED
                question.validation_notes = f"Skipped after {question.attempts} invalid attempts"
                
                return {
                    "status": "skipped",
                    "message": "I'll skip that question for now.",
                    "question_id": question_id,
                    "next_question": self.get_next_question()
                }
            else:
                return {
                    "status": "invalid",
                    "message": message,
                    "question_id": question_id,
                    "attempts": question.attempts
                }
    
    def _handle_follow_up(self, question: Question, answer: str, parsed_data: Optional[Dict]):
        """Handle conditional follow-up questions based on answer"""
        
        if not question.conditional:
            return
        
        condition = question.conditional
        condition_met = False
        
        # Check if answer meets condition
        if "if_answer_contains" in condition:
            answer_lower = answer.lower()
            for keyword in condition["if_answer_contains"]:
                if keyword in answer_lower:
                    condition_met = True
                    break
        
        # Add follow-up to queue if condition met
        if condition_met and question.follow_up:
            follow_up_question = Question(
                id=question.id + 100,  # Unique ID for follow-ups
                category=f"{question.category}_details",
                question_text=question.follow_up,
                validation_rules={"type": "text", "required": False},
                status=QuestionStatus.PENDING
            )
            self.question_queue.insert(0, follow_up_question)
            self.skip_log.append({
                "parent_question": question.id,
                "follow_up_added": True,
                "condition": condition.get("if_answer_contains")
            })
    
    def get_active_question(self) -> Optional[Question]:
        """Get the question currently being asked (status=ASKED)"""
        # Check queue for active questions
        for q in self.question_queue:
            if q.status == QuestionStatus.ASKED:
                return q
        
        # Check main list
        for q in self.questions:
            if q.status == QuestionStatus.ASKED:
                return q
        
        # Only if none are ASKED, try to get the next PENDING one
        # but don't mark it yet
        for q in self.questions[self.current_question_index:]:
            if q.status == QuestionStatus.PENDING:
                return q
        
        return None

    def get_next_question(self, mark_as_asked: bool = True) -> Optional[Question]:
        """Get the next question to ask"""
        
        # Check queue first
        if self.question_queue:
            next_q = self.question_queue.pop(0)
            if mark_as_asked:
                next_q.status = QuestionStatus.ASKED
            return next_q
        
        # Find next pending question
        for q in self.questions[self.current_question_index:]:
            if q.status == QuestionStatus.PENDING:
                if mark_as_asked:
                    q.status = QuestionStatus.ASKED
                    self.current_question_index = self.questions.index(q)
                return q
        
        # Check if any questions need re-asking
        for q in self.questions:
            if q.status == QuestionStatus.REASK:
                if mark_as_asked:
                    q.status = QuestionStatus.ASKED
                return q
        
        return None
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """Get question by ID"""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None
    
    def get_progress(self) -> Dict:
        """Get current progress tracking"""
        total = len(self.questions)
        answered = sum(1 for q in self.questions if q.status == QuestionStatus.ANSWERED)
        skipped = sum(1 for q in self.questions if q.status == QuestionStatus.SKIPPED)
        pending = sum(1 for q in self.questions if q.status == QuestionStatus.PENDING)
        
        completion_rate = answered / total if total > 0 else 0
        
        # Calculate category completion
        categories_completed = len(self.completed_categories)
        total_categories = len(set(q.category for q in self.questions))
        
        # Get answered questions with details
        answered_questions = [
            {
                "id": q.id,
                "category": q.category,
                "question": q.question_text,
                "answer": q.answer,
                "confidence": q.answer_confidence,
                "validation_notes": q.validation_notes
            }
            for q in self.questions
            if q.status == QuestionStatus.ANSWERED
        ]
        
        return {
            "total_questions": total,
            "answered": answered,
            "skipped": skipped,
            "pending": pending,
            "completion_rate": completion_rate,
            "categories_completed": categories_completed,
            "total_categories": total_categories,
            "answered_questions": answered_questions,
            "remaining_categories": [
                q.category for q in self.questions 
                if q.status not in [QuestionStatus.ANSWERED, QuestionStatus.SKIPPED]
                and q.category not in self.completed_categories
            ][:5]  # Show first 5
        }
    
    def get_structured_responses(self) -> List[Dict]:
        """Get all answered questions in structured format"""
        return [
            {
                "question_id": q.id,
                "category": q.category,
                "question": q.question_text,
                "answer": q.answer,
                "confidence": q.answer_confidence,
                "validation_notes": q.validation_notes,
                "status": q.status.value
            }
            for q in self.questions
            if q.status == QuestionStatus.ANSWERED
        ]
    
    def reset(self):
        """Reset all questions for new call"""
        for q in self.questions:
            q.status = QuestionStatus.PENDING
            q.answer = None
            q.answer_confidence = 0.0
            q.validation_notes = None
            q.attempts = 0
        
        self.current_question_index = 0
        self.question_queue = []
        self.completed_categories = set()
        self.skip_log = []
    
    def is_complete(self) -> bool:
        """Check if all required questions are answered"""
        required_questions = [q for q in self.questions if q.validation_rules.get("required", False)]
        answered_required = sum(1 for q in required_questions if q.status == QuestionStatus.ANSWERED)
        return answered_required == len(required_questions)
