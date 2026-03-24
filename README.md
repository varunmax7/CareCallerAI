# 🎙️ CareCaller AI Voice Agent Simulator

CareCaller is a high-performance AI Voice Agent designed for healthcare medication check-ins. It automates patient follow-ups, captures vital signs, and manages prescription refills through a natural voice interface.

## 🚀 Key Features
- **👂 Speech-to-Text (STT)**: Powered by OpenAI Whisper for lightning-fast transcription.
- **🧠 Agent Core**: Intelligent LLM-based logic for health questionnaire flow management.
- **🗣️ Text-to-Speech (TTS)**: High-quality, natural-sounding voice generation.
- **🏢 Professional Reporting**: Automated PDF and JSON report generation for each call.
- **🛡️ Identity Verification**: Built-in verification steps to ensure patient privacy.

## 🛠️ How to Run
1. **Clone the repo**: `git clone https://github.com/varunmax7/CareCallerAI.git`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up environment**: Create a `.env` file with your `OPENAI_API_KEY`.
4. **Launch Simulator**: `python3 -m streamlit run final_simulator.py`

## 📂 Project Structure
- `final_simulator.py`: Main entry point (Streamlit UI).
- `agent_core.py`: Central logic for the AI assistant.
- `stt_engine.py` & `tts_engine.py`: Audio processing modules.
- `question_controller.py`: Manages the 14-question healthcare flow.
- `context_memory.py`: Patient profile and history tracking.

---
Built with ❤️ for the 2026 Hackathon.
