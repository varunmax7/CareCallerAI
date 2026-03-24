# test_agent.py
import os
from dotenv import load_dotenv
from agent_core import VoiceAgent
import json

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ Please set OPENAI_API_KEY in .env file")
    exit(1)

# Create agent
agent = VoiceAgent(api_key, model="gpt-4o-mini")

print("\n" + "="*60)
print("🤖 AI Voice Agent Test")
print("="*60)
print("\nSimulating a patient call...\n")

# Simulate conversation
test_conversation = [
    "Hello?",
    "Yes, this is John Smith",
    "I'm doing okay, a bit tired lately",
    "My weight is 185 pounds",
    "No side effects really",
    "No allergies that I know of",
    "Yes, I take it every day",
    "No new medications",
    "No, I haven't been hospitalized",
    "I saw my doctor last month",
    "Yes, 120 over 80",
    "Just the tiredness mostly",
    "Yes, I need a refill",
    "It's working fine",
    "Appetite is normal",
    "Sleep has been okay",
    "No other concerns"
]

print("🤖 Agent: Hello! This is CareCaller. Am I speaking with John Smith?\n")

for i, user_input in enumerate(test_conversation):
    print(f"👤 Patient: {user_input}")
    
    # Process user input
    response = agent.process_user_input(user_input)
    
    print(f"🤖 Agent: {response['agent_message']}\n")
    
    # Stop after 5 exchanges or if call ends
    if i > 10 or not agent.call_active:
        break

print("\n" + "="*60)
print("📊 Call Summary")
print("="*60)

# Show completion status
completion = agent.get_completion_status()
print(f"\nQuestions Completed: {completion['answered']}/{completion['total_questions']}")
print(f"Completion Rate: {completion['completion_rate']:.1%}")

# Show structured output
structured = agent.get_structured_output()
print(f"\nCall Outcome: {structured['conversation_summary']['final_outcome']}")

print("\n📝 Structured Responses:")
print(json.dumps(structured['responses'], indent=2))

# Save to file
with open("test_output.json", "w") as f:
    json.dump(structured, f, indent=2)
print("\n✅ Output saved to test_output.json")
