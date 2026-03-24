# test_stt.py
import os
from dotenv import load_dotenv
from stt_engine import STTEngine

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ Please set OPENAI_API_KEY in .env file")
    exit(1)

# Create STT engine
stt = STTEngine(api_key)

print("\n" + "="*50)
print("Speech-to-Text Test")
print("="*50)

while True:
    print("\nOptions:")
    print("1. Record until Enter")
    print("2. Record 5 seconds")
    print("3. Exit")
    
    choice = input("\nChoose (1-3): ")
    
    if choice == "1":
        text = stt.record_and_transcribe()
        print(f"\n📝 You said: {text}")
        
    elif choice == "2":
        text = stt.record_and_transcribe(duration=5)
        print(f"\n📝 You said: {text}")
        
    elif choice == "3":
        print("Goodbye!")
        break
