# response_storage.py
import json
import csv
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

class AnswerConfidence(Enum):
    HIGH = "high"       # Clear, direct answer
    MEDIUM = "medium"   # Answer provided but slightly unclear
    LOW = "low"         # Vague or uncertain answer
    MISSING = "missing" # No answer provided

@dataclass
class Answer:
    """Individual answer structure"""
    question_id: int
    question_text: str
    category: str
    answer: Optional[str] = None
    confidence: AnswerConfidence = AnswerConfidence.MISSING
    confidence_score: float = 0.0
    source: str = ""  # "direct", "inferred", "follow_up", "default"
    validation_notes: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            "question_id": self.question_id,
            "question": self.question_text,
            "category": self.category,
            "answer": self.answer,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "validation_notes": self.validation_notes,
            "timestamp": self.timestamp
        }

@dataclass
class CallRecord:
    """Complete call record matching training data format"""
    call_id: str
    call_duration: int
    outcome: str
    transcript_text: str
    responses_json: List[Dict]
    whisper_mismatch_count: int = 0
    response_completeness: float = 0.0
    validation_notes: str = ""
    has_ticket: bool = False
    ticket_category: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary matching training data format"""
        return {
            "call_id": self.call_id,
            "call_duration": self.call_duration,
            "outcome": self.outcome,
            "transcript_text": self.transcript_text,
            "responses_json": self.responses_json,
            "whisper_mismatch_count": self.whisper_mismatch_count,
            "response_completeness": self.response_completeness,
            "validation_notes": self.validation_notes,
            "has_ticket": self.has_ticket,
            "ticket_category": self.ticket_category,
            **self.metadata
        }

class ResponseStorage:
    """Main storage system for structured responses"""
    
    # Standard 14 questions from training data
    STANDARD_QUESTIONS = [
        {"id": 1, "category": "weight", "question": "What is your current weight?"},
        {"id": 2, "category": "side_effects", "question": "Have you experienced any side effects?"},
        {"id": 3, "category": "allergies", "question": "Do you have any medication allergies?"},
        {"id": 4, "category": "medication_taken", "question": "Are you taking your medication as prescribed?"},
        {"id": 5, "category": "new_medications", "question": "Have you started any new medications?"},
        {"id": 6, "category": "hospitalization", "question": "Have you been hospitalized recently?"},
        {"id": 7, "category": "doctor_visit", "question": "Have you seen your doctor recently?"},
        {"id": 8, "category": "blood_pressure", "question": "What is your blood pressure?"},
        {"id": 9, "category": "symptoms", "question": "Are you experiencing any new symptoms?"},
        {"id": 10, "category": "refill_timing", "question": "Do you need a refill now?"},
        {"id": 11, "category": "medication_effectiveness", "question": "Is your medication working?"},
        {"id": 12, "category": "appetite", "question": "How is your appetite?"},
        {"id": 13, "category": "sleep", "question": "How is your sleep?"},
        {"id": 14, "category": "concerns", "question": "Do you have any other concerns?"}
    ]
    
    def __init__(self, call_id: Optional[str] = None):
        """Initialize response storage"""
        self.call_id = call_id or self._generate_call_id()
        self.answers: Dict[int, Answer] = {}
        self.conversation_history: List[Dict] = []
        self.start_time = datetime.now()
        self.end_time = None
        self.validation_notes = []
        
        # Initialize with standard questions
        self._initialize_questions()
        
        # Tracking for completeness
        self.mapped_responses = []
        self.uncertain_answers = []
        self.incomplete_answers = []
    
    def _generate_call_id(self) -> str:
        """Generate unique call ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6]
        return f"CALL_{timestamp}_{random_hash}"
    
    def _initialize_questions(self):
        """Initialize all 14 questions"""
        for q in self.STANDARD_QUESTIONS:
            self.answers[q["id"]] = Answer(
                question_id=q["id"],
                question_text=q["question"],
                category=q["category"]
            )
    
    def add_answer(self, question_id: int, answer: str, 
                   confidence: AnswerConfidence = AnswerConfidence.HIGH,
                   confidence_score: float = 0.9,
                   source: str = "direct",
                   validation_note: Optional[str] = None) -> Answer:
        """Add or update an answer for a question"""
        
        if question_id not in self.answers:
            # If question not found, add it (for dynamic questions)
            self.answers[question_id] = Answer(
                question_id=question_id,
                question_text=f"Question {question_id}",
                category="custom"
            )
        
        answer_obj = self.answers[question_id]
        answer_obj.answer = answer
        answer_obj.confidence = confidence
        answer_obj.confidence_score = confidence_score
        answer_obj.source = source
        answer_obj.validation_notes = validation_note
        answer_obj.timestamp = datetime.now().isoformat()
        
        # Track uncertain answers
        if confidence in [AnswerConfidence.LOW, AnswerConfidence.MISSING]:
            self.uncertain_answers.append(answer_obj)
        
        return answer_obj
    
    def map_conversation_to_questions(self, conversation: List[Dict]) -> Dict[int, str]:
        """Map conversation messages to relevant questions"""
        mapping = {}
        
        # Define keywords for each question category
        category_keywords = {
            "weight": ["weight", "pounds", "lbs", "kg", "scale"],
            "side_effects": ["side effect", "reaction", "nausea", "dizzy", "headache"],
            "allergies": ["allergic", "allergy", "reaction", "rash"],
            "medication_taken": ["take medication", "pill", "dose", "prescribed"],
            "new_medications": ["new medication", "started taking", "prescribed"],
            "hospitalization": ["hospital", "admitted", "emergency room", "er"],
            "doctor_visit": ["doctor", "appointment", "saw doctor", "visit"],
            "blood_pressure": ["blood pressure", "bp", "pressure reading"],
            "symptoms": ["symptom", "feeling", "pain", "ache"],
            "refill_timing": ["refill", "need more", "running out", "prescription"],
            "medication_effectiveness": ["working", "effective", "helping"],
            "appetite": ["appetite", "eating", "hungry"],
            "sleep": ["sleep", "rest", "insomnia", "tired"],
            "concerns": ["concern", "worry", "question", "other"]
        }
        
        # Search conversation for relevant answers
        for message in conversation:
            if message.get("role") == "patient":
                content = message.get("content", "").lower()
                
                for category, keywords in category_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        # Find question ID for this category
                        for q in self.STANDARD_QUESTIONS:
                            if q["category"] == category:
                                mapping[q["id"]] = content
                                break
        
        return mapping
    
    def calculate_confidence(self, answer: str, source: str, context: str = "") -> tuple[AnswerConfidence, float, str]:
        """Calculate confidence score for an answer"""
        
        if not answer or answer.strip() == "":
            return AnswerConfidence.MISSING, 0.0, "No answer provided"
        
        answer_lower = answer.lower()
        confidence_score = 0.5  # Base
        notes = []
        
        # Check for vague answers
        vague_patterns = ["i don't know", "not sure", "maybe", "i guess", "probably"]
        if any(pattern in answer_lower for pattern in vague_patterns):
            confidence_score -= 0.3
            notes.append("Vague answer detected")
        
        # Check answer length
        if len(answer) < 3:
            confidence_score -= 0.2
            notes.append("Very short answer")
        elif len(answer) > 20:
            confidence_score += 0.1
            notes.append("Detailed answer")
        
        # Check for numbers (good for weight, BP)
        import re
        if re.search(r'\d+', answer):
            confidence_score += 0.1
            notes.append("Contains numeric data")
        
        # Source-based adjustment
        if source == "direct":
            confidence_score += 0.1
            notes.append("Direct answer")
        elif source == "inferred":
            confidence_score -= 0.1
            notes.append("Inferred from conversation")
        elif source == "follow_up":
            confidence_score += 0.05
            notes.append("From follow-up question")
        
        # Context-based adjustment
        if context:
            confidence_score += 0.05
            notes.append("Context available")
        
        # Normalize score
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Determine confidence level
        if confidence_score >= 0.8:
            confidence_level = AnswerConfidence.HIGH
        elif confidence_score >= 0.5:
            confidence_level = AnswerConfidence.MEDIUM
        else:
            confidence_level = AnswerConfidence.LOW
        
        return confidence_level, confidence_score, ", ".join(notes) if notes else "Clear answer"
    
    def add_conversation_turn(self, role: str, content: str):
        """Add conversation turn to history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_answered_questions(self) -> List[Answer]:
        """Get all answered questions"""
        return [a for a in self.answers.values() if a.answer is not None]
    
    def get_missing_questions(self) -> List[Answer]:
        """Get all unanswered questions"""
        return [a for a in self.answers.values() if a.answer is None]
    
    def get_completeness_score(self) -> float:
        """Calculate response completeness (0-1)"""
        answered = len(self.get_answered_questions())
        total = len(self.answers)
        return answered / total if total > 0 else 0.0
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score based on confidence"""
        answered = self.get_answered_questions()
        if not answered:
            return 0.0
        
        total_score = sum(a.confidence_score for a in answered)
        return total_score / len(answered)
    
    def flag_issues(self) -> List[str]:
        """Flag any issues with responses"""
        issues = []
        
        # Check for missing questions
        missing = self.get_missing_questions()
        if missing:
            issues.append(f"Missing {len(missing)} questions: {', '.join([q.category for q in missing[:5]])}")
        
        # Check for low confidence answers
        low_confidence = [a for a in self.get_answered_questions() if a.confidence == AnswerConfidence.LOW]
        if low_confidence:
            issues.append(f"{len(low_confidence)} answers with low confidence")
        
        # Check for validation notes
        for a in self.get_answered_questions():
            if a.validation_notes and "error" in a.validation_notes.lower():
                issues.append(f"Validation issue with {a.category}: {a.validation_notes}")
        
        return issues
    
    def to_json(self, include_conversation: bool = True) -> Dict:
        """Convert to JSON format matching training data"""
        
        # Format responses as expected by training data
        responses_json = []
        for answer in self.answers.values():
            response = {
                "question": answer.question_text,
                "category": answer.category,
                "answer": answer.answer,
                "confidence": answer.confidence_score,
                "source": answer.source
            }
            responses_json.append(response)
        
        # Build transcript
        transcript_lines = []
        for msg in self.conversation_history:
            role = "AGENT" if msg["role"] == "agent" else "USER"
            transcript_lines.append(f"[{role}]: {msg['content']}")
        transcript_text = "\n".join(transcript_lines)
        
        # Build complete record matching hackathon schema
        record = {
            "call_id": self.call_id,
            "call_duration": int((datetime.now() - self.start_time).total_seconds()),
            "outcome": self._determine_outcome(),
            "transcript_text": transcript_text,
            "whisper_transcript": " ".join([msg["content"] for msg in self.conversation_history]),
            "whisper_mismatch_count": 0,  # Fixed for simulation
            "responses_json": responses_json,
            "response_completeness": self.get_completeness_score(),
            "quality_score": self.get_quality_score(),
            "validation_notes": "\n".join(self.validation_notes + self.flag_issues()),
            "has_ticket": len(self.flag_issues()) > 0,
            "ticket_category": self._determine_ticket_category() if len(self.flag_issues()) > 0 else None,
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": (self.end_time or datetime.now()).isoformat(),
                "total_turns": len(self.conversation_history),
                "answered_questions": len(self.get_answered_questions()),
                "missing_questions": len(self.get_missing_questions()),
                "uncertain_answers": len(self.uncertain_answers)
            }
        }
        
        if include_conversation:
            record["conversation_history"] = self.conversation_history
        
        return record
    
    def _determine_outcome(self) -> str:
        """Determine call outcome based on conversation"""
        # This should be determined by the actual call outcome
        # Placeholder logic
        if self.get_completeness_score() >= 0.8:
            return "completed"
        elif self.get_completeness_score() >= 0.5:
            return "incomplete"
        else:
            return "failed"
    
    def _determine_ticket_category(self) -> Optional[str]:
        """Determine ticket category if issues found"""
        issues = self.flag_issues()
        if not issues:
            return None
        
        # Categorize issues
        missing = self.get_missing_questions()
        low_conf = [a for a in self.get_answered_questions() if a.confidence == AnswerConfidence.LOW]
        
        if missing and len(missing) > 2:
            return "agent_skipped_questions"
        elif low_conf and len(low_conf) > 3:
            return "data_capture_errors"
        elif any("weight" in issue for issue in issues):
            return "stt_mishearing"
        else:
            return "outcome_miscategorization"
    
    def export_to_csv(self, filename: str):
        """Export responses to CSV"""
        data = []
        for answer in self.answers.values():
            data.append({
                "call_id": self.call_id,
                "question_id": answer.question_id,
                "question": answer.question_text,
                "category": answer.category,
                "answer": answer.answer,
                "confidence": answer.confidence_score,
                "confidence_level": answer.confidence.value,
                "source": answer.source,
                "validation_notes": answer.validation_notes
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return filename
    
    def export_to_json(self, filename: str):
        """Export full call record to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.to_json(), f, indent=2)
        return filename
    
    def generate_summary(self) -> Dict:
        """Generate human-readable summary"""
        answered = self.get_answered_questions()
        missing = self.get_missing_questions()
        
        return {
            "call_id": self.call_id,
            "summary": {
                "total_questions": len(self.answers),
                "answered": len(answered),
                "missing": len(missing),
                "completeness": f"{self.get_completeness_score():.1%}",
                "quality": f"{self.get_quality_score():.1%}"
            },
            "answered_questions": [
                {
                    "category": a.category,
                    "question": a.question_text,
                    "answer": a.answer,
                    "confidence": a.confidence.value
                }
                for a in answered
            ],
            "missing_questions": [
                {
                    "category": a.category,
                    "question": a.question_text
                }
                for a in missing
            ],
            "issues": self.flag_issues(),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving responses"""
        recommendations = []
        
        missing = self.get_missing_questions()
        if missing:
            recommendations.append(f"Ask about: {', '.join([q.category for q in missing[:3]])}")
        
        low_confidence = [a for a in self.get_answered_questions() if a.confidence == AnswerConfidence.LOW]
        if low_confidence:
            recommendations.append(f"Clarify answers for: {', '.join([a.category for a in low_confidence[:3]])}")
        
        if self.get_completeness_score() < 0.7:
            recommendations.append("Complete all required health questions")
        
        return recommendations
    
    def reset(self):
        """Reset storage for new call"""
        self.__init__(call_id=self._generate_call_id())
    
    def validate_against_training_format(self) -> Dict:
        """Validate that output matches training data format"""
        record = self.to_json()
        
        required_fields = [
            "call_id", "call_duration", "outcome", "transcript_text",
            "responses_json", "response_completeness", "validation_notes"
        ]
        
        missing_fields = [f for f in required_fields if f not in record]
        
        # Validate responses_json structure
        responses_valid = True
        if "responses_json" in record:
            for resp in record["responses_json"]:
                if not all(k in resp for k in ["question", "answer", "confidence"]):
                    responses_valid = False
                    break
        
        return {
            "valid": len(missing_fields) == 0 and responses_valid,
            "missing_fields": missing_fields,
            "responses_valid": responses_valid,
            "record_structure": list(record.keys())
        }
