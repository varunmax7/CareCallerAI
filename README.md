# 🎙️ CareCaller AI — Voice Agent Simulator

> **Problem 2: AI Voice Agent Simulator** — CareCaller Hackathon 2026
>
> A production-grade AI voice agent that conducts patient medication refill check-in calls with human-like conversation flow, real-time edge case handling, and clinical-grade structured data extraction.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green.svg)](https://openai.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why CareCaller Stands Out](#-why-carecaller-stands-out)
- [Architecture](#-architecture)
- [Core Features](#-core-features)
- [Evaluation Criteria Mapping](#-evaluation-criteria-mapping)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [How to Run](#-how-to-run)
- [Live Demo Walkthrough](#-live-demo-walkthrough)
- [Safety & Compliance](#-safety--compliance)

---

## 🌟 Overview

CareCaller is not just a chatbot. It is a **full-duplex AI voice agent simulator** purpose-built for healthcare medication refill check-ins. It listens to the patient through a microphone (STT), thinks using an LLM with deep contextual memory (Agent Core), and responds with a natural human voice (TTS) — all orchestrated through a real-time Streamlit dashboard.

The agent was designed by studying the **35 reference transcripts** (`transcript_samples.json`) and the **689-call training dataset** to replicate real-world conversation patterns, question flows, and edge case handling observed in production pharmacy calls.

### 🎯 What It Does

| Capability | Description |
|---|---|
| **Identity Verification** | Greets patient by name, confirms identity through multi-step flow |
| **14-Question Health Check** | Asks all 14 structured questionnaire questions naturally |
| **Off-Script Handling** | Detects and professionally handles pricing, dosage, and side-effect queries |
| **Structured Data Capture** | Extracts and structures all 14 responses into JSON matching training data format |
| **Escalation Intelligence** | Knows when to escalate (emergency) vs. continue (routine) vs. end (opt-out) |
| **Edge Case Coverage** | Handles reschedule, opt-out, wrong number, complaint, technical issues |
| **Professional Reporting** | Generates downloadable PDF and JSON call summaries |

---

## 🏆 Why CareCaller Stands Out

### 1. 🧠 Hybrid Intelligence (Rule-Based + LLM)
Most hackathon solutions use *only* an LLM to handle everything, which leads to hallucinations, missed questions, and unpredictable behavior. **CareCaller uses a hybrid approach:**

- **Rule-based systems** handle deterministic logic: question flow sequencing, answer validation, edge case pattern matching, and compliance checks.
- **GPT-4o** handles *only* what it's best at: generating natural language, understanding ambiguous patient responses, and managing conversational tone.

> This means the agent **never skips a question**, **never gives medical advice**, and **never fails to detect an emergency** — because those are handled by deterministic code, not probabilistic LLM outputs.

### 2. 🔄 Stateful Question Flow Controller
Unlike simple prompt-chaining approaches, CareCaller has a dedicated `QuestionFlowController` with:

- **14 individually defined questions** with category-specific validation rules (numeric ranges for weight, BP format validation, choice matching)
- **Conditional follow-up logic** — if a patient says "yes" to side effects, the agent automatically queues a follow-up ("Can you describe them?")
- **Re-ask & skip logic** — unclear answers get re-asked (up to 2 attempts), then gracefully skipped to avoid frustrating the patient
- **Progress tracking** — real-time completion percentage visible in the UI sidebar

### 3. 🛡️ Enterprise-Grade Edge Case Handler
The `EdgeCaseHandler` doesn't just check for keywords — it uses **regex pattern matching with confidence scoring** across 8 distinct edge case categories:

| Edge Case | Detection | Action |
|---|---|---|
| 🚨 Emergency | `chest pain`, `can't breathe`, `seizure` | Immediate escalation, call ends |
| 🚫 Opt-Out | `stop calling`, `not interested`, `remove me` | Graceful goodbye, preferences updated |
| 📅 Reschedule | `call back later`, `busy now`, `not a good time` | Captures preferred day/time |
| ❌ Wrong Number | `wrong number`, `not this person` | Apologizes and flags record |
| 💊 Medical Advice | `should I take`, `is it safe`, `what dosage` | Redirects to doctor (never gives advice) |
| 💰 Pricing | `how much`, `insurance`, `co-pay` | Transfers to billing department |
| 😡 Complaint | `unhappy`, `speak to manager` | Escalates to human supervisor |
| 🔧 Technical | `can't hear`, `breaking up` | Repeats message more clearly |

### 4. 🧠 Context Memory System
Most solutions treat each turn independently. CareCaller maintains a **living memory** across the entire call:

- **Patient Profile Builder**: Automatically extracts and structures medications, allergies, weight, blood pressure from natural speech
- **Topic Coverage Tracker**: Monitors which health categories have been discussed to ensure completeness
- **Topic Switch Detector**: Identifies when a patient goes off-script and queues the off-topic item for handling without losing the question flow
- **Entity Extraction**: Pulls numbers, dates, medication names, and symptoms from every message
- **Importance Scoring**: Ranks messages by importance (0-1) to prioritize critical information
- **Context Window for LLM**: Provides the LLM with a structured summary of the conversation, patient profile, and topic status — not a raw transcript dump

### 5. 📊 Training-Data-Compatible Output
The structured JSON output **exactly matches the hackathon training data schema**:

```json
{
  "call_id": "CALL_20260325_120000_abc123",
  "call_duration": 245,
  "outcome": "completed",
  "transcript_text": "[AGENT]: Hello!...\n[USER]: Yes...",
  "responses_json": [
    {"question": "What is your current weight?", "answer": "185 pounds", "confidence": 0.9},
    ...
  ],
  "response_completeness": 0.93,
  "validation_notes": "...",
  "has_ticket": false
}
```

This means output can be **directly fed into Problem 1's ticket prediction model** for cross-problem integration.

### 6. 🗣️ Full Voice Pipeline (Not Just Text)
Many solutions demo text-only chat. CareCaller implements the **complete voice loop**:

```
🎤 Patient speaks → Whisper STT → Agent Core → GPT-4o TTS → 🔊 Agent speaks
```

- **OpenAI Whisper**: Real-time transcription at 16kHz with English language optimization
- **OpenAI TTS**: Multiple voice options (Shimmer, Alloy, Nova, Echo) with adjustable speed
- **Audio Caching**: Common phrases are cached as MP3 files to eliminate redundant API calls and reduce latency
- **Async Playback**: TTS plays in a background thread so the UI remains responsive

### 7. ✅ Post-Call Validation System
After every call, a `ValidationSystem` runs **6 automated checks**:

| Check | What It Does |
|---|---|
| Question Coverage | Verifies all 14 questions were attempted |
| Answer Validity | Validates formats (weight in range, BP format, yes/no) |
| Agent Behavior | Scans for prohibited patterns (medical advice, unprofessional language) |
| Call Metrics | Flags calls that are too short (<30s) or too long (>10min) |
| Data Quality | Detects vague answers and conflicting information |
| Compliance | Checks for HIPAA violations (SSN/payment requests) |

This produces a **quality score (0-100)** and determines if a review ticket is needed — directly mapping to the `has_ticket` target variable in the training data.

### 8. 📄 Professional Clinical Reports
One-click generation of:
- **PDF Report**: Branded document with patient info, questionnaire results, clinical notes, and full transcript
- **JSON Export**: Machine-readable structured data for EHR integration
- **CSV Export**: Tabular format for analytics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (final_simulator.py)            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Chat UI  │  │ Agent State  │  │ Progress │  │ Reporting │  │
│  │ (Bubbles)│  │  Inspector   │  │  Sidebar │  │ PDF/JSON  │  │
│  └────┬─────┘  └──────────────┘  └──────────┘  └───────────┘  │
│       │                                                         │
├───────┼─────────────────────────────────────────────────────────┤
│       ▼                                                         │
│  ┌─────────┐     ┌─────────────────────┐     ┌──────────┐      │
│  │   STT   │────▶│     AGENT CORE      │────▶│   TTS    │      │
│  │ Whisper │     │   (Orchestrator)    │     │  OpenAI  │      │
│  └─────────┘     │                     │     └──────────┘      │
│                  │  ┌───────────────┐  │                        │
│                  │  │  GPT-4o LLM   │  │                        │
│                  │  │  (Natural NLU)│  │                        │
│                  │  └───────────────┘  │                        │
│                  │                     │                        │
│                  │  ┌───────────────┐  │  ┌─────────────────┐  │
│                  │  │   Question    │  │  │  Context Memory  │  │
│                  │  │  Controller   │  │  │  • Patient Profile│  │
│                  │  │  (14 Q Flow)  │  │  │  • Topic Tracker  │  │
│                  │  └───────────────┘  │  │  • Entity Extract │  │
│                  │                     │  └─────────────────┘  │
│                  │  ┌───────────────┐  │  ┌─────────────────┐  │
│                  │  │  Edge Case    │  │  │ Response Storage │  │
│                  │  │  Handler      │  │  │ • JSON/CSV/PDF   │  │
│                  │  │  (8 types)    │  │  │ • Schema Match   │  │
│                  │  └───────────────┘  │  └─────────────────┘  │
│                  │                     │  ┌─────────────────┐  │
│                  │  ┌───────────────┐  │  │  Validation      │  │
│                  │  │  Identity     │  │  │  System          │  │
│                  │  │  Verifier     │  │  │  • 6 auto checks │  │
│                  │  └───────────────┘  │  │  • Ticket logic  │  │
│                  └─────────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Core Features

### 📋 14-Point Health Questionnaire

| # | Category | Question | Validation |
|---|---|---|---|
| 1 | Weight | Have you checked your weight recently? | Numeric (50-500 lbs) |
| 2 | Side Effects | Have you experienced any side effects? | Text + conditional follow-up |
| 3 | Allergies | Have you had any allergic reactions? | Text + conditional follow-up |
| 4 | Medication Adherence | Are you taking your medication as prescribed? | Choice (yes/no/sometimes) |
| 5 | New Medications | Have you started any new medications? | Text + conditional follow-up |
| 6 | Hospitalization | Have you been hospitalized recently? | Text + conditional follow-up |
| 7 | Doctor Visit | Have you seen your doctor recently? | Text + conditional follow-up |
| 8 | Blood Pressure | Have you checked your blood pressure? | BP format (systolic/diastolic) |
| 9 | Symptoms | Are you experiencing any new symptoms? | Text + conditional follow-up |
| 10 | Refill Timing | Do you need a refill now? | Choice (yes/no/soon) |
| 11 | Medication Effectiveness | Is your medication working well? | Choice + conditional follow-up |
| 12 | Appetite | Have you noticed changes in appetite? | Text + conditional follow-up |
| 13 | Sleep | How has your sleep been lately? | Text + conditional follow-up |
| 14 | Concerns | Do you have any other health concerns? | Open text |

### 🔊 Voice Pipeline

- **Input**: Real-time microphone recording via `sounddevice` at 16kHz
- **STT**: OpenAI Whisper API with English language optimization
- **Processing**: Hybrid rule-based + LLM response generation
- **TTS**: OpenAI TTS with 4 selectable voices and adjustable speed (0.5x–1.5x)
- **Output**: Async audio playback via `pygame` with interrupt support

### 🖥️ Interactive Dashboard

- **Chat History**: Color-coded agent/patient bubbles with auto-scroll
- **Agent State Inspector**: Real-time view of patient profile, edge case detections, and decision logic
- **Progress Sidebar**: Live question completion bar and topic coverage checklist
- **Dual Input Mode**: Voice (microphone) or keyboard for flexible demo scenarios

---

## 📊 Evaluation Criteria Mapping

### Conversation Quality (30%) ✅
| Requirement | Implementation |
|---|---|
| Natural flow | GPT-4o generates conversational responses, not scripted text |
| Appropriate responses | System prompt enforces empathetic, professional healthcare tone |
| Handles interruptions | Topic switch detection + off-topic queue preserves conversation state |

### Response Accuracy (30%) ✅
| Requirement | Implementation |
|---|---|
| Captures all 14 answers | `QuestionFlowController` tracks each question individually with status |
| Structured output | `ResponseStorage` generates JSON matching `responses_json` training format |
| Confidence scoring | Multi-factor confidence calculation (answer length, clarity, source, context) |

### Edge Case Handling (20%) ✅
| Requirement | Implementation |
|---|---|
| Pricing questions | Regex detection → transfers to billing |
| Reschedules | Extracts day/time → captures scheduling preference |
| Opt-outs | Graceful goodbye → updates preferences |
| Escalations | Emergency keyword detection → immediate human handoff |

### Technical Implementation (10%) ✅
| Requirement | Implementation |
|---|---|
| Code quality | Modular architecture with 9 focused Python modules |
| Architecture | Separation of concerns: STT, Core, TTS, Memory, Validation are independent |
| Documentation | This README + inline docstrings + type hints throughout |

### Demo & Presentation (10%) ✅
| Requirement | Implementation |
|---|---|
| Live demo | Streamlit simulator with voice + keyboard input |
| Simulated call | Full end-to-end call flow visible in the dashboard |

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.9+ | Core development language |
| **LLM** | OpenAI GPT-4o-mini | Natural language understanding and generation |
| **STT** | OpenAI Whisper | Real-time speech-to-text transcription |
| **TTS** | OpenAI TTS-1 | Natural voice synthesis with multiple voice options |
| **UI Framework** | Streamlit | Interactive dashboard and real-time visualization |
| **Audio Capture** | sounddevice + numpy | Microphone recording and audio processing |
| **Audio Playback** | pygame | MP3 audio playback with async support |
| **PDF Generation** | fpdf2 | Professional clinical report generation |
| **Data Handling** | pandas | Structured data manipulation and CSV export |
| **Visualization** | plotly | Advanced charts and analytics (extensible) |
| **Environment** | python-dotenv | Secure API key management |

---

## 📂 Project Structure

```text
CareCallerAI/
├── final_simulator.py        # 🖥️  Main Entry Point — Streamlit UI & call orchestration
├── agent_core.py             # 🧠  Central Agent — LLM orchestration, identity flow, response logic
├── stt_engine.py             # 🎤  Speech-to-Text — Whisper integration, mic recording
├── tts_engine.py             # 🔊  Text-to-Speech — Voice synthesis, caching, async playback
├── question_controller.py    # 📋  Question Flow — 14 questions, validation rules, follow-ups
├── context_memory.py         # 🧠  Context Memory — Patient profile, topic tracking, entities
├── edge_case_handler.py      # 🛡️  Edge Cases — 8 types, regex detection, confidence scoring
├── response_storage.py       # 💾  Data Storage — JSON/CSV export, schema validation
├── validation_system.py      # ✅  Validation — 6 post-call checks, ticket determination
├── requirements.txt          # 📦  Dependencies
├── .env                      # 🔑  API Keys (not committed)
├── .gitignore                # 🚫  Ignored files
└── README.md                 # 📖  This file
```

### Module Sizes (Lines of Code)

| Module | Lines | Responsibility |
|---|---|---|
| `question_controller.py` | 583 | Question flow, validation rules, conditional logic |
| `validation_system.py` | 587 | Post-call quality checks and ticket determination |
| `context_memory.py` | 544 | Patient profile, topic tracking, entity extraction |
| `response_storage.py` | 492 | Structured data export matching training schema |
| `final_simulator.py` | 431 | Streamlit UI, call orchestration, PDF generation |
| `agent_core.py` | 428 | Central agent logic, LLM calls, state management |
| `edge_case_handler.py` | 427 | Edge case detection across 8 categories |
| `tts_engine.py` | 292 | Voice synthesis with caching and async playback |
| `stt_engine.py` | 155 | Microphone recording and Whisper transcription |
| **Total** | **~3,940** | **Complete implementation** |

---

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- An OpenAI API key with GPT-4o and Whisper access
- A working microphone (for voice mode)

### 1. Clone the Repository
```bash
git clone https://github.com/varunmax7/CareCallerAI.git
cd CareCallerAI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. Launch the Simulator
```bash
streamlit run final_simulator.py
```

The app opens at `http://localhost:8501`.

---

## 🎬 Live Demo Walkthrough

1. **Start Call** → Click "📞 Start Call" — Agent greets the patient by name
2. **Verify Identity** → Say "Yes, this is him" — Agent confirms and begins health check
3. **Answer Questions** → Respond naturally — Agent asks all 14 questions with follow-ups
4. **Test Edge Cases** → Try:
   - "How much does my medication cost?" → Pricing redirect
   - "I'm having chest pain" → Emergency escalation
   - "Call me back tomorrow" → Reschedule capture
   - "Stop calling me" → Opt-out handling
5. **End Call** → Agent wraps up and generates reports
6. **Download Reports** → Click "📥 JSON" or "📄 PDF" to export clinical summaries

---

## 🛡️ Safety & Compliance

- ❌ **Never gives medical advice** — Always redirects to healthcare provider
- ❌ **Never requests PHI** — No SSN, payment info, or sensitive data collection
- ✅ **Identity verification** — Every call starts with patient confirmation
- ✅ **Emergency detection** — Immediate escalation for life-threatening keywords
- ✅ **Compliance validation** — Post-call scan for HIPAA violations

> **Note**: CareCaller is a **simulator** built for the hackathon. In a production environment, it would integrate with HIPAA-compliant infrastructure, encrypted communication channels, and authenticated EHR APIs.

---

## 👨‍💻 Author

Built with ❤️ by [Varun](https://github.com/varunmax7) for the **CareCaller Hackathon 2026**.

---

*"The best voice agent isn't the one that sounds the most human — it's the one that never misses a question, never gives bad advice, and always knows when to ask for help."*
