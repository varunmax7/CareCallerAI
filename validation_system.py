# validation_system.py
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

class ValidationSeverity(Enum):
    CRITICAL = "critical"    # Must be fixed, creates ticket
    HIGH = "high"            # Likely creates ticket
    MEDIUM = "medium"        # Might create ticket
    LOW = "low"              # Informational only
    INFO = "info"            # Just for logging

class ValidationCategory(Enum):
    QUESTION_COVERAGE = "question_coverage"
    ANSWER_VALIDITY = "answer_validity"
    AGENT_BEHAVIOR = "agent_behavior"
    CALL_METRICS = "call_metrics"
    DATA_QUALITY = "data_quality"
    COMPLIANCE = "compliance"

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    category: ValidationCategory
    severity: ValidationSeverity
    issue_type: str
    description: str
    location: Optional[str] = None
    details: Optional[Dict] = None
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "description": self.description,
            "location": self.location,
            "details": self.details,
            "recommendation": self.recommendation
        }

@dataclass
class ValidationReport:
    """Complete validation report"""
    call_id: str
    timestamp: datetime
    overall_score: float  # 0-100
    is_valid: bool
    issues: List[ValidationIssue]
    metrics: Dict[str, Any]
    recommendations: List[str]
    ticket_needed: bool
    ticket_category: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "call_id": self.call_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "ticket_needed": self.ticket_needed,
            "ticket_category": self.ticket_category
        }

class ValidationSystem:
    """Main validation system for call quality"""
    
    # Standard questions that must be attempted
    REQUIRED_QUESTIONS = list(range(1, 15))  # 1-14
    
    # Answer format validation patterns
    VALIDATION_PATTERNS = {
        "weight": {
            "pattern": r'\b(\d{2,3})\s*(?:lbs?|pounds?|kg?)?\b',
            "type": "numeric",
            "range": (50, 500),
            "description": "Weight should be between 50-500 lbs"
        },
        "blood_pressure": {
            "pattern": r'(\d{2,3})\s*[/over]+\s*(\d{2,3})',
            "type": "bp",
            "range": {"systolic": (90, 200), "diastolic": (60, 120)},
            "description": "BP should be in format like 120/80"
        },
        "yes_no": {
            "pattern": r'\b(yes|no|yeah|nope|correct|incorrect)\b',
            "type": "choice",
            "options": ["yes", "no", "yeah", "nope"],
            "description": "Should be yes/no response"
        },
        "date": {
            "pattern": r'\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2})\b',
            "type": "date",
            "description": "Should specify a date or day"
        },
        "number": {
            "pattern": r'\d+',
            "type": "numeric",
            "description": "Should contain a number"
        }
    }
    
    # Prohibited agent behaviors
    PROHIBITED_PATTERNS = {
        "medical_advice": [
            r'\b(you should take|i recommend|try taking|prescribe)\b',
            r'\b(it\'?s safe to|you can take|go ahead and)\b',
            r'\b(medical advice|diagnosis|treatment for)\b'
        ],
        "unprofessional": [
            r'\b(omg|wow|seriously|whatever)\b',
            r'\b(you messed up|wrong|incorrect)\b'
        ]
    }
    
    def __init__(self):
        """Initialize validation system"""
        self.reset()
    
    def reset(self):
        """Reset for new call"""
        self.issues = []
        self.metrics = {
            "questions_attempted": 0,
            "questions_answered": 0,
            "questions_valid": 0,
            "total_questions": 14,
            "call_duration_seconds": 0,
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "agent_medical_advice_count": 0,
            "unclear_answers_count": 0,
            "validation_errors": []
        }
    
    def validate_call(self, call_data: Dict) -> ValidationReport:
        """Validate complete call data"""
        self.reset()
        
        call_id = call_data.get("call_id", "unknown")
        transcript = call_data.get("transcript_text", "")
        responses = call_data.get("responses_json", [])
        duration = call_data.get("call_duration", 0)
        agent_messages = self._extract_agent_messages(transcript)
        patient_messages = self._extract_patient_messages(transcript)
        
        # Run all validations
        self._validate_question_coverage(responses)
        self._validate_answer_formats(responses)
        self._validate_agent_behavior(agent_messages)
        self._validate_call_metrics(duration, responses)
        self._validate_data_quality(responses, patient_messages)
        self._validate_compliance(agent_messages)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score()
        
        # Determine if ticket needed
        ticket_needed, ticket_category = self._determine_ticket_needed()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = ValidationReport(
            call_id=call_id,
            timestamp=datetime.now(),
            overall_score=overall_score,
            is_valid=overall_score >= 70.0,
            issues=self.issues,
            metrics=self.metrics,
            recommendations=recommendations,
            ticket_needed=ticket_needed,
            ticket_category=ticket_category
        )
        
        return report
    
    def _extract_agent_messages(self, transcript: str) -> List[str]:
        """Extract agent messages from transcript"""
        messages = []
        pattern = r'\[AGENT\]:\s*(.*?)(?=\n\[|\Z)'
        matches = re.findall(pattern, transcript, re.DOTALL)
        return [m.strip() for m in matches]
    
    def _extract_patient_messages(self, transcript: str) -> List[str]:
        """Extract patient messages from transcript"""
        messages = []
        pattern = r'\[USER\]:\s*(.*?)(?=\n\[|\Z)'
        matches = re.findall(pattern, transcript, re.DOTALL)
        return [m.strip() for m in matches]
    
    def _validate_question_coverage(self, responses: List[Dict]):
        """Validate all 14 questions were attempted"""
        answered_questions = set()
        for resp in responses:
            if resp.get("answer") and resp.get("answer") != "":
                # Extract question ID from question text
                question_text = resp.get("question", "")
                for q_id in self.REQUIRED_QUESTIONS:
                    if f"Q{q_id}" in question_text or self._match_question(question_text, q_id):
                        answered_questions.add(q_id)
                        break
        
        self.metrics["questions_answered"] = len(answered_questions)
        
        # Check for missing questions
        missing_questions = set(self.REQUIRED_QUESTIONS) - answered_questions
        
        if missing_questions:
            severity = ValidationSeverity.HIGH if len(missing_questions) > 3 else ValidationSeverity.MEDIUM
            
            self.issues.append(ValidationIssue(
                category=ValidationCategory.QUESTION_COVERAGE,
                severity=severity,
                issue_type="missing_questions",
                description=f"Missing {len(missing_questions)} required questions",
                location="questionnaire",
                details={"missing_question_ids": list(missing_questions)},
                recommendation=f"Ask about: {', '.join([f'Q{q}' for q in missing_questions])}"
            ))
        
        # Calculate completeness
        self.metrics["completeness_score"] = len(answered_questions) / 14.0
    
    def _match_question(self, question_text: str, q_id: int) -> bool:
        """Match question text to question ID"""
        # Simplified matching
        question_map = {
            1: ["weight"],
            2: ["side effect"],
            3: ["allerg"],
            4: ["medication", "taking"],
            5: ["new medication"],
            6: ["hospital"],
            7: ["doctor"],
            8: ["blood pressure"],
            9: ["symptom"],
            10: ["refill"],
            11: ["working", "effective"],
            12: ["appetite"],
            13: ["sleep"],
            14: ["concern"]
        }
        
        question_lower = question_text.lower()
        keywords = question_map.get(q_id, [])
        return any(kw in question_lower for kw in keywords)
    
    def _validate_answer_formats(self, responses: List[Dict]):
        """Validate answer formats"""
        valid_count = 0
        
        for resp in responses:
            answer = str(resp.get("answer", ""))
            if not answer or answer == "None":
                continue
            
            # Try to validate based on question
            question = resp.get("question", "").lower()
            is_valid = True
            validation_note = ""
            
            # Weight validation
            if "weight" in question:
                match = re.search(self.VALIDATION_PATTERNS["weight"]["pattern"], answer)
                if match:
                    weight = int(match.group(1))
                    range_min, range_max = self.VALIDATION_PATTERNS["weight"]["range"]
                    if range_min <= weight <= range_max:
                        valid_count += 1
                        is_valid = True
                    else:
                        validation_note = f"Weight {weight} outside normal range"
                        is_valid = False
                else:
                    validation_note = "Weight format invalid"
                    is_valid = False
            
            # Blood pressure validation
            elif "blood pressure" in question or "bp" in question:
                match = re.search(self.VALIDATION_PATTERNS["blood_pressure"]["pattern"], answer)
                if match:
                    systolic = int(match.group(1))
                    diastolic = int(match.group(2))
                    range_sys = self.VALIDATION_PATTERNS["blood_pressure"]["range"]["systolic"]
                    range_dia = self.VALIDATION_PATTERNS["blood_pressure"]["range"]["diastolic"]
                    
                    if range_sys[0] <= systolic <= range_sys[1] and range_dia[0] <= diastolic <= range_dia[1]:
                        valid_count += 1
                        is_valid = True
                    else:
                        validation_note = f"BP {systolic}/{diastolic} outside normal range"
                        is_valid = False
                else:
                    validation_note = "BP format invalid"
                    is_valid = False
            
            # Yes/No validation
            elif any(word in question for word in ["any", "have you", "are you", "do you"]):
                match = re.search(self.VALIDATION_PATTERNS["yes_no"]["pattern"], answer, re.IGNORECASE)
                if match:
                    valid_count += 1
                    is_valid = True
                else:
                    validation_note = "Expected yes/no response"
                    is_valid = False
            
            else:
                # Generic text validation
                if len(answer) > 2:
                    valid_count += 1
                else:
                    validation_note = "Answer too short"
                    is_valid = False
            
            if not is_valid:
                self.issues.append(ValidationIssue(
                    category=ValidationCategory.ANSWER_VALIDITY,
                    severity=ValidationSeverity.MEDIUM,
                    issue_type="invalid_format",
                    description=validation_note or "Answer format invalid",
                    location=question,
                    details={"answer": answer},
                    recommendation="Re-ask question or verify format"
                ))
                self.metrics["validation_errors"].append(validation_note)
        
        self.metrics["questions_valid"] = valid_count
    
    def _validate_agent_behavior(self, agent_messages: List[str]):
        """Validate agent behavior (no medical advice, etc.)"""
        
        for message in agent_messages:
            message_lower = message.lower()
            
            # Check for prohibited patterns
            for violation_type, patterns in self.PROHIBITED_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        self.issues.append(ValidationIssue(
                            category=ValidationCategory.AGENT_BEHAVIOR,
                            severity=ValidationSeverity.CRITICAL,
                            issue_type=violation_type,
                            description=f"Agent gave {violation_type.replace('_', ' ')}",
                            location=message[:100],
                            details={"pattern": pattern, "message": message[:200]},
                            recommendation="Never provide medical advice. Always redirect to doctor."
                        ))
                        
                        if violation_type == "medical_advice":
                            self.metrics["agent_medical_advice_count"] += 1
    
    def _validate_call_metrics(self, duration: int, responses: List[Dict]):
        """Validate call metrics like duration, completeness"""
        
        self.metrics["call_duration_seconds"] = duration
        
        # Duration validation
        if duration < 30 and duration > 0:
            self.issues.append(ValidationIssue(
                category=ValidationCategory.CALL_METRICS,
                severity=ValidationSeverity.MEDIUM,
                issue_type="call_too_short",
                description=f"Call duration ({duration}s) is too short",
                recommendation="Ensure all questions are asked"
            ))
        elif duration > 600:  # 10 minutes
            self.issues.append(ValidationIssue(
                category=ValidationCategory.CALL_METRICS,
                severity=ValidationSeverity.LOW,
                issue_type="call_too_long",
                description=f"Call duration ({duration}s) is unusually long",
                recommendation="Review for efficiency improvements"
            ))
        
        # Completeness validation
        completeness = self.metrics["completeness_score"]
        if completeness < 0.5:
            self.issues.append(ValidationIssue(
                category=ValidationCategory.CALL_METRICS,
                severity=ValidationSeverity.HIGH,
                issue_type="low_completeness",
                description=f"Only {completeness:.0%} of questions answered",
                recommendation="Ensure all required questions are asked"
            ))
    
    def _validate_data_quality(self, responses: List[Dict], patient_messages: List[str]):
        """Validate data quality and consistency"""
        
        # Check for unclear answers
        unclear_count = 0
        for resp in responses:
            answer = str(resp.get("answer", ""))
            if answer and any(word in answer.lower() for word in ["i don't know", "not sure", "maybe", "guess"]):
                unclear_count += 1
                self.issues.append(ValidationIssue(
                    category=ValidationCategory.DATA_QUALITY,
                    severity=ValidationSeverity.MEDIUM,
                    issue_type="unclear_answer",
                    description=f"Unclear answer: {answer[:50]}...",
                    recommendation="Ask follow-up for clarification"
                ))
        
        self.metrics["unclear_answers_count"] = unclear_count
        
        # Check for conflicting information
        self._check_conflicts(responses)
    
    def _check_conflicts(self, responses: List[Dict]):
        """Check for conflicting answers"""
        # Simplified conflict detection
        for resp in responses:
            question = resp.get("question", "")
            answer = str(resp.get("answer", ""))
            if "side effect" in question.lower() and "no" in answer.lower():
                # Check if later they mention side effects
                for other in responses:
                    if "symptom" in other.get("question", "").lower():
                        if "yes" in str(other.get("answer", "")).lower():
                            self.issues.append(ValidationIssue(
                                category=ValidationCategory.DATA_QUALITY,
                                severity=ValidationSeverity.HIGH,
                                issue_type="conflicting_answers",
                                description="Patient said no side effects but later reported symptoms",
                                recommendation="Clarify during call"
                            ))
    
    def _validate_compliance(self, agent_messages: List[str]):
        """Validate compliance with regulations"""
        
        # Check for HIPAA violations
        phi_patterns = [
            r'\b(ssn|social security)\b',
            r'\b(credit card|payment info)\b'
        ]
        
        for message in agent_messages:
            message_lower = message.lower()
            for pattern in phi_patterns:
                if re.search(pattern, message_lower):
                    self.issues.append(ValidationIssue(
                        category=ValidationCategory.COMPLIANCE,
                        severity=ValidationSeverity.CRITICAL,
                        issue_type="phi_exposure",
                        description="Agent requested sensitive information",
                        recommendation="Never ask for SSN or payment info"
                    ))
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Deduct for issues based on severity
        for issue in self.issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 30
            elif issue.severity == ValidationSeverity.HIGH:
                score -= 15
            elif issue.severity == ValidationSeverity.MEDIUM:
                score -= 8
            elif issue.severity == ValidationSeverity.LOW:
                score -= 3
        
        # Add completeness bonus
        score += self.metrics["completeness_score"] * 10
        
        # Add quality bonus
        if self.metrics["questions_valid"] > 0:
            quality_ratio = self.metrics["questions_valid"] / max(1, self.metrics["questions_answered"])
            score += quality_ratio * 10
        
        # Cap at 0-100
        self.metrics["quality_score"] = max(0, min(100, score))
        
        return self.metrics["quality_score"]
    
    def _determine_ticket_needed(self) -> Tuple[bool, Optional[str]]:
        """Determine if a review ticket is needed"""
        
        # Check for critical issues
        critical_issues = [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            return True, "critical_violation"
        
        # Check for high severity issues
        high_issues = [i for i in self.issues if i.severity == ValidationSeverity.HIGH]
        if len(high_issues) >= 2:
            return True, "multiple_high_severity_issues"
        
        # Check for low completeness
        if self.metrics["completeness_score"] < 0.6:
            return True, "incomplete_call"
        
        # Check for medical advice
        if self.metrics["agent_medical_advice_count"] > 0:
            return True, "agent_gave_medical_advice"
        
        # Check for many unclear answers
        if self.metrics["unclear_answers_count"] > 3:
            return True, "unclear_answers"
        
        # Default
        return False, None
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Based on completeness
        if self.metrics["completeness_score"] < 0.8:
            recommendations.append("Complete all 14 required health questions")
        
        # Based on answer quality
        if self.metrics["questions_valid"] < self.metrics["questions_answered"]:
            recommendations.append("Verify answer formats (weights should be numbers, BP in format 120/80)")
        
        # Based on agent behavior
        if self.metrics["agent_medical_advice_count"] > 0:
            recommendations.append("Never provide medical advice. Always redirect to doctor")
        
        # Based on unclear answers
        if self.metrics["unclear_answers_count"] > 2:
            recommendations.append("Ask follow-up questions for unclear answers")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Call quality is good. Continue current approach")
        
        return recommendations
    
    def generate_post_call_summary(self, report: ValidationReport) -> str:
        """Generate human-readable post-call summary"""
        
        summary = []
        summary.append("=" * 60)
        summary.append(f"POST-CALL SUMMARY - {report.call_id}")
        summary.append("=" * 60)
        summary.append(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Overall Score: {report.overall_score:.1f}/100")
        summary.append(f"Status: {'✅ PASSED' if report.is_valid else '❌ NEEDS REVIEW'}")
        summary.append("")
        
        # Metrics
        summary.append("📊 METRICS:")
        summary.append(f"  • Questions Completed: {self.metrics['questions_answered']}/14")
        summary.append(f"  • Completeness: {self.metrics['completeness_score']:.1%}")
        summary.append(f"  • Valid Answers: {self.metrics['questions_valid']}/{self.metrics['questions_answered']}")
        summary.append(f"  • Call Duration: {self.metrics['call_duration_seconds']} seconds")
        summary.append(f"  • Unclear Answers: {self.metrics['unclear_answers_count']}")
        summary.append("")
        
        # Issues
        if report.issues:
            summary.append("⚠️ ISSUES DETECTED:")
            for issue in report.issues:
                summary.append(f"  [{issue.severity.value.upper()}] {issue.description}")
                if issue.recommendation:
                    summary.append(f"    → {issue.recommendation}")
            summary.append("")
        
        # Recommendations
        if report.recommendations:
            summary.append("💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                summary.append(f"  • {rec}")
            summary.append("")
        
        # Ticket info
        if report.ticket_needed:
            summary.append("🎫 REVIEW TICKET NEEDED")
            summary.append(f"  Category: {report.ticket_category}")
            summary.append("  Action: Human review required")
        else:
            summary.append("✅ No review ticket needed")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)
