# context_memory.py
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib
from collections import deque

class TopicCategory(Enum):
    IDENTITY = "identity"
    MEDICATION = "medication"
    SIDE_EFFECTS = "side_effects"
    VITALS = "vitals"
    APPOINTMENT = "appointment"
    GENERAL = "general"
    CONCERN = "concern"
    OFF_SCRIPT = "off_script"

class ConversationTurn(Enum):
    AGENT = "agent"
    PATIENT = "patient"

@dataclass
class Message:
    """Single message in conversation"""
    role: str  # "agent" or "patient"
    content: str
    timestamp: datetime
    topic: Optional[TopicCategory] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0-1 scale
    intent: Optional[str] = None

@dataclass
class TopicCoverage:
    """Track coverage of a topic"""
    topic: TopicCategory
    covered: bool = False
    last_mentioned: Optional[datetime] = None
    mentions: int = 0
    key_points: List[str] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    confidence: float = 0.0

@dataclass
class PatientProfile:
    """Structured patient information"""
    name: Optional[str] = None
    confirmed: bool = False
    medications: List[Dict] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    last_refill: Optional[str] = None
    pharmacy: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    # Vital signs history
    weight_history: List[Dict] = field(default_factory=list)
    bp_history: List[Dict] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update(self, key: str, value: Any):
        """Update patient profile field"""
        if hasattr(self, key):
            setattr(self, key, value)
            self.updated_at = datetime.now()
    
    def add_medication(self, name: str, details: Optional[Dict] = None):
        """Add medication to profile"""
        self.medications.append({
            "name": name,
            "details": details or {},
            "added_at": datetime.now().isoformat()
        })
    
    def add_allergy(self, allergy: str):
        """Add allergy to profile"""
        if allergy not in self.allergies:
            self.allergies.append(allergy)
    
    def add_weight(self, weight: float, units: str = "lbs"):
        """Add weight reading"""
        self.weight_history.append({
            "weight": weight,
            "units": units,
            "date": datetime.now().isoformat()
        })
    
    def add_bp(self, systolic: int, diastolic: int):
        """Add blood pressure reading"""
        self.bp_history.append({
            "systolic": systolic,
            "diastolic": diastolic,
            "date": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "confirmed": self.confirmed,
            "medications": self.medications,
            "allergies": self.allergies,
            "conditions": self.conditions,
            "last_refill": self.last_refill,
            "pharmacy": self.pharmacy,
            "preferred_time": self.preferred_time,
            "notes": self.notes,
            "weight_history": self.weight_history[-5:],  # Last 5 entries
            "bp_history": self.bp_history[-5:],  # Last 5 entries
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class ContextMemory:
    def __init__(self, max_history: int = 20, summarize_threshold: int = 15):
        """Initialize context memory system"""
        self.max_history = max_history
        self.summarize_threshold = summarize_threshold
        self.messages: deque = deque(maxlen=max_history)
        self.patient_profile = PatientProfile()
        self.topic_coverage: Dict[TopicCategory, TopicCoverage] = {}
        self.context_summary: str = ""
        self.current_topic: Optional[TopicCategory] = None
        self.topic_switches: List[Dict] = []
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        
        # Initialize topic tracking
        for topic in TopicCategory:
            self.topic_coverage[topic] = TopicCoverage(topic=topic)
        
        # Track off-topic conversations
        self.off_topic_queue: List[Dict] = []
        
        # Entity tracking
        self.extracted_entities: Dict[str, Any] = {
            "numbers": [],
            "dates": [],
            "medications": [],
            "symptoms": [],
            "questions": []
        }
        
    def add_message(self, role: str, content: str, 
                    topic: Optional[TopicCategory] = None,
                    entities: Optional[Dict] = None,
                    intent: Optional[str] = None) -> Message:
        """Add a message to conversation history"""
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            topic=topic or self._detect_topic(content),
            entities=entities or self._extract_entities(content),
            intent=intent or self._detect_intent(content, role),
            importance=self._calculate_importance(content, role)
        )
        
        self.messages.append(message)
        
        # Update topic coverage
        if message.topic:
            self._update_topic_coverage(message)
        
        # Update current topic
        if role == "patient":
            self.current_topic = message.topic
        
        # Check for topic switch
        if len(self.messages) > 1:
            self._check_topic_switch(message)
        
        # Update patient profile with extracted info
        self._update_profile_from_message(message)
        
        # Update summary if needed
        if len(self.messages) >= self.summarize_threshold:
            self._update_summary()
        
        return message
    
    def _detect_topic(self, content: str) -> TopicCategory:
        """Detect topic from message content"""
        content_lower = content.lower()
        
        topic_keywords = {
            TopicCategory.IDENTITY: ["name", "call", "speak", "this is", "i am", "myself"],
            TopicCategory.MEDICATION: ["medication", "medicine", "pill", "prescription", "refill", "dosage"],
            TopicCategory.SIDE_EFFECTS: ["side effect", "reaction", "nausea", "dizzy", "headache", "feeling"],
            TopicCategory.VITALS: ["weight", "blood pressure", "bp", "pressure", "vital", "reading"],
            TopicCategory.APPOINTMENT: ["appointment", "schedule", "reschedule", "time", "call back", "later"],
            TopicCategory.CONCERN: ["concern", "worried", "problem", "issue", "help", "emergency"],
            TopicCategory.OFF_SCRIPT: ["price", "cost", "insurance", "bill", "payment", "why"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return topic
        
        return TopicCategory.GENERAL
    
    def _extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract entities from message"""
        entities = {}
        content_lower = content.lower()
        
        # Extract numbers
        import re
        numbers = re.findall(r'\d+', content)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # Extract weight patterns
        weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?|kg?)', content_lower)
        if weight_match:
            entities["weight"] = {
                "value": int(weight_match.group(1)),
                "unit": "lbs" if "lbs" in content_lower or "pound" in content_lower else "kg"
            }
        
        # Extract blood pressure
        bp_match = re.search(r'(\d{2,3})\s*[/over]+\s*(\d{2,3})', content_lower)
        if bp_match:
            entities["blood_pressure"] = {
                "systolic": int(bp_match.group(1)),
                "diastolic": int(bp_match.group(2))
            }
        
        # Extract medication names (simple pattern)
        med_patterns = ["aspirin", "ibuprofen", "lisinopril", "metformin", "atorvastatin"]
        found_meds = [med for med in med_patterns if med in content_lower]
        if found_meds:
            entities["medications"] = found_meds
        
        # Extract dates
        date_match = re.search(r'(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}\/\d{1,2})', content_lower)
        if date_match:
            entities["date"] = date_match.group(1)
        
        return entities
    
    def _detect_intent(self, content: str, role: str) -> str:
        """Detect user intent from message"""
        if role == "agent":
            return "response"
        
        content_lower = content.lower()
        
        intents = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "confirmation": ["yes", "yeah", "correct", "right", "that's right"],
            "negation": ["no", "not", "nope", "never"],
            "question": ["what", "why", "when", "where", "how", "?"],
            "clarification": ["repeat", "again", "sorry", "what did you say"],
            "opt_out": ["stop", "opt out", "don't want", "not interested"],
            "emergency": ["emergency", "urgent", "chest pain", "can't breathe"],
            "reschedule": ["reschedule", "later", "another time", "busy now"]
        }
        
        for intent, keywords in intents.items():
            if any(keyword in content_lower for keyword in keywords):
                return intent
        
        return "statement"
    
    def _calculate_importance(self, content: str, role: str) -> float:
        """Calculate message importance (0-1)"""
        importance = 0.3  # Base importance
        
        # Longer messages are more important
        if len(content) > 50:
            importance += 0.2
        if len(content) > 100:
            importance += 0.1
        
        # Patient messages are more important than agent
        if role == "patient":
            importance += 0.2
        
        # Messages with entities are important
        entities = self._extract_entities(content)
        if entities:
            importance += min(0.3, len(entities) * 0.1)
        
        # Urgent keywords
        urgent_keywords = ["emergency", "urgent", "important", "chest pain", "bleeding"]
        if any(keyword in content.lower() for keyword in urgent_keywords):
            importance = 1.0
        
        return min(1.0, importance)
    
    def _update_topic_coverage(self, message: Message):
        """Update topic coverage based on message"""
        if message.topic:
            coverage = self.topic_coverage[message.topic]
            coverage.mentions += 1
            coverage.last_mentioned = message.timestamp
            
            # Mark as covered if message contains meaningful content
            if len(message.content) > 10 and message.role == "patient":
                coverage.covered = True
                coverage.confidence = min(1.0, coverage.confidence + 0.3)
                
                # Extract key points
                if message.importance > 0.6:
                    key_point = message.content[:100]
                    if key_point not in coverage.key_points:
                        coverage.key_points.append(key_point)
    
    def _check_topic_switch(self, new_message: Message):
        """Detect and handle topic switches"""
        if len(self.messages) < 2:
            return
        
        prev_message = self.messages[-2]
        
        if (new_message.topic and prev_message.topic and 
            new_message.topic != prev_message.topic):
            
            topic_switch = {
                "from": prev_message.topic.value,
                "to": new_message.topic.value,
                "timestamp": new_message.timestamp.isoformat(),
                "message": new_message.content[:100]
            }
            self.topic_switches.append(topic_switch)
            
            # If patient switched topic, store off-topic content
            if new_message.role == "patient" and new_message.topic != self.current_topic:
                self.off_topic_queue.append({
                    "topic": new_message.topic.value,
                    "content": new_message.content,
                    "timestamp": new_message.timestamp.isoformat()
                })
    
    def _update_profile_from_message(self, message: Message):
        """Extract and update patient profile from message"""
        if message.role != "patient":
            return
        
        content = message.content.lower()
        entities = message.entities
        
        # Extract name
        if not self.patient_profile.name:
            name_patterns = ["this is", "i am", "my name is", "speaking"]
            for pattern in name_patterns:
                if pattern in content:
                    name_start = content.find(pattern) + len(pattern)
                    name = content[name_start:].strip().split()[0]
                    if name and len(name) > 1:
                        self.patient_profile.name = name.title()
                        break
        
        # Extract weight
        if "weight" in entities and "weight" in entities["weight"]:
            weight_data = entities["weight"]
            self.patient_profile.add_weight(
                weight_data["value"], 
                weight_data.get("unit", "lbs")
            )
        
        # Extract blood pressure
        if "blood_pressure" in entities:
            bp = entities["blood_pressure"]
            self.patient_profile.add_bp(bp["systolic"], bp["diastolic"])
        
        # Extract medications
        if "medications" in entities:
            for med in entities["medications"]:
                self.patient_profile.add_medication(med)
        
        # Extract allergies
        allergy_keywords = ["allergic to", "allergy to", "reaction to"]
        for keyword in allergy_keywords:
            if keyword in content:
                allergy = content.split(keyword)[-1].strip().split(".")[0]
                if allergy and len(allergy) < 50:
                    self.patient_profile.add_allergy(allergy)
    
    def _update_summary(self):
        """Generate conversation summary"""
        recent_messages = list(self.messages)[-10:]
        
        summary_parts = []
        
        # Key topics covered
        covered_topics = [t for t, c in self.topic_coverage.items() if c.covered]
        if covered_topics:
            summary_parts.append(f"Topics covered: {', '.join([t.value for t in covered_topics])}")
        
        # Patient info summary
        if self.patient_profile.name:
            summary_parts.append(f"Patient: {self.patient_profile.name}")
        if self.patient_profile.medications:
            meds = [m["name"] for m in self.patient_profile.medications[-3:]]
            summary_parts.append(f"Medications: {', '.join(meds)}")
        
        # Recent important points
        important_messages = [m for m in recent_messages if m.importance > 0.7]
        if important_messages:
            summary_parts.append("Key points:")
            for msg in important_messages[-3:]:
                summary_parts.append(f"- {msg.content[:100]}")
        
        self.context_summary = "\n".join(summary_parts)
    
    def get_recent_context(self, n: int = 5) -> List[Message]:
        """Get most recent n messages"""
        return list(self.messages)[-n:]
    
    def get_conversation_summary(self) -> str:
        """Get formatted conversation summary"""
        if not self.context_summary:
            self._update_summary()
        return self.context_summary
    
    def get_patient_context(self) -> str:
        """Get patient profile as context string"""
        profile = self.patient_profile.to_dict()
        
        context_parts = []
        
        if profile["name"]:
            context_parts.append(f"Patient name: {profile['name']}")
        
        if profile["medications"]:
            meds = [m["name"] for m in profile["medications"][-3:]]
            context_parts.append(f"Current medications: {', '.join(meds)}")
        
        if profile["allergies"]:
            context_parts.append(f"Allergies: {', '.join(profile['allergies'])}")
        
        if profile["weight_history"]:
            last_weight = profile["weight_history"][-1]
            context_parts.append(f"Last weight: {last_weight['weight']} {last_weight['units']}")
        
        if profile["bp_history"]:
            last_bp = profile["bp_history"][-1]
            context_parts.append(f"Last BP: {last_bp['systolic']}/{last_bp['diastolic']}")
        
        return "\n".join(context_parts) if context_parts else "No patient information collected yet"
    
    def get_topic_status(self) -> Dict:
        """Get status of all topics"""
        return {
            topic.value: {
                "covered": coverage.covered,
                "mentions": coverage.mentions,
                "key_points": coverage.key_points[-3:],
                "confidence": coverage.confidence
            }
            for topic, coverage in self.topic_coverage.items()
        }
    
    def get_uncovered_topics(self) -> List[str]:
        """Get topics that haven't been covered"""
        return [
            topic.value for topic, coverage in self.topic_coverage.items()
            if not coverage.covered and topic != TopicCategory.GENERAL
        ]
    
    def get_topic_switches_summary(self) -> List[Dict]:
        """Get summary of topic switches"""
        return self.topic_switches[-5:]  # Last 5 switches
    
    def get_off_topic_queue(self) -> List[Dict]:
        """Get off-topic messages that need handling"""
        return self.off_topic_queue[-5:]  # Last 5 off-topic messages
    
    def get_context_for_llm(self) -> str:
        """Get formatted context for LLM prompt"""
        context = []
        
        # Add conversation summary
        context.append("=== CONVERSATION SUMMARY ===")
        context.append(self.get_conversation_summary())
        
        # Add patient profile
        context.append("\n=== PATIENT PROFILE ===")
        context.append(self.get_patient_context())
        
        # Add topic status
        context.append("\n=== TOPIC COVERAGE ===")
        uncovered = self.get_uncovered_topics()
        if uncovered:
            context.append(f"Still need to cover: {', '.join(uncovered[:3])}")
        
        # Add recent topic switches
        switches = self.get_topic_switches_summary()
        if switches:
            context.append("\n=== RECENT TOPIC SWITCHES ===")
            for switch in switches[-2:]:
                context.append(f"Switched from {switch['from']} to {switch['to']}")
        
        # Add recent messages
        context.append("\n=== RECENT CONVERSATION ===")
        for msg in self.get_recent_context(5):
            role = "Agent" if msg.role == "agent" else "Patient"
            context.append(f"{role}: {msg.content[:100]}")
        
        return "\n".join(context)
    
    def reset(self):
        """Reset context for new call"""
        self.messages.clear()
        self.patient_profile = PatientProfile()
        self.topic_coverage = {}
        self.context_summary = ""
        self.current_topic = None
        self.topic_switches = []
        self.off_topic_queue = []
        self.extracted_entities = {k: [] for k in self.extracted_entities}
        
        # Reinitialize topic coverage
        for topic in TopicCategory:
            self.topic_coverage[topic] = TopicCoverage(topic=topic)
    
    def to_dict(self) -> Dict:
        """Export context as dictionary"""
        return {
            "session_id": self.session_id,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "topic": m.topic.value if m.topic else None,
                    "importance": m.importance
                }
                for m in self.messages
            ],
            "patient_profile": self.patient_profile.to_dict(),
            "topic_status": self.get_topic_status(),
            "topic_switches": self.topic_switches,
            "context_summary": self.context_summary
        }
