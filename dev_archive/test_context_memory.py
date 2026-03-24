# test_context_memory.py
from context_memory import ContextMemory, TopicCategory
import json
import time

def test_context_memory():
    """Test the context memory system with various scenarios"""
    
    print("\n" + "="*60)
    print("🧠 Context Memory System Test")
    print("="*60)
    
    memory = ContextMemory()
    
    # Test scenario 1: Normal conversation flow
    print("\n1️⃣ Testing normal conversation flow...")
    print("-" * 40)
    
    conversation = [
        ("agent", "Hello, this is CareCaller. Am I speaking with John Smith?"),
        ("patient", "Yes, this is John Smith speaking."),
        ("agent", "Great. How are you feeling today?"),
        ("patient", "I'm doing okay, but I've been a bit tired lately."),
        ("agent", "Have you checked your weight recently?"),
        ("patient", "Yes, I'm 185 pounds."),
        ("agent", "Any side effects from your medication?"),
        ("patient", "No side effects to report."),
        ("agent", "Do you need a refill?"),
        ("patient", "Yes, I need a refill soon."),
        ("agent", "What's your preferred pharmacy?"),
        ("patient", "CVS on Main Street."),
    ]
    
    for role, content in conversation:
        message = memory.add_message(role, content)
        print(f"{role.upper()}: {content[:60]}...")
        time.sleep(0.1)
    
    # Show context
    print("\n📊 Conversation Summary:")
    print(memory.get_conversation_summary())
    
    print("\n👤 Patient Profile:")
    print(memory.get_patient_context())
    
    # Test scenario 2: Topic switching
    print("\n\n2️⃣ Testing topic switching...")
    print("-" * 40)
    
    topic_switches = [
        ("agent", "Let me check your medication details."),
        ("patient", "Actually, how much does this medication cost?"),
        ("agent", "I understand you're asking about pricing. I'll need to transfer you to billing."),
        ("patient", "No, wait, I also wanted to ask about side effects again."),
        ("agent", "Of course, what side effects are you concerned about?"),
    ]
    
    for role, content in topic_switches:
        message = memory.add_message(role, content)
        print(f"{role.upper()}: {content}")
        time.sleep(0.1)
    
    # Show topic switches
    switches = memory.get_topic_switches_summary()
    print("\n🔄 Topic Switches Detected:")
    for switch in switches:
        print(f"  From {switch['from']} → {switch['to']}")
    
    # Test scenario 3: Off-topic handling
    print("\n\n3️⃣ Testing off-topic handling...")
    print("-" * 40)
    
    off_topic = [
        ("patient", "By the way, what's the weather like today?"),
        ("agent", "I'm here to help with your medication. Let's focus on your health."),
        ("patient", "Sorry, just wondering. Anyway, my medication is working well."),
    ]
    
    for role, content in off_topic:
        message = memory.add_message(role, content)
        print(f"{role.upper()}: {content}")
        time.sleep(0.1)
    
    # Show off-topic queue
    off_topic_queue = memory.get_off_topic_queue()
    if off_topic_queue:
        print("\n📋 Off-topic Messages:")
        for item in off_topic_queue:
            print(f"  Topic: {item['topic']} - {item['content'][:50]}...")
    
    # Test scenario 4: Information extraction
    print("\n\n4️⃣ Testing information extraction...")
    print("-" * 40)
    
    info_messages = [
        ("patient", "I'm allergic to penicillin and aspirin."),
        ("patient", "My blood pressure was 135 over 85 yesterday."),
        ("patient", "I take lisinopril and metformin daily."),
    ]
    
    for role, content in info_messages:
        message = memory.add_message(role, content)
        print(f"{role.upper()}: {content}")
        print(f"  Extracted: {json.dumps(message.entities, indent=2)}")
        time.sleep(0.1)
    
    # Show final patient profile
    print("\n\n📋 Final Patient Profile:")
    print(json.dumps(memory.patient_profile.to_dict(), indent=2))
    
    # Show topic coverage
    print("\n📊 Topic Coverage Status:")
    status = memory.get_topic_status()
    for topic, coverage in status.items():
        if coverage['covered']:
            print(f"  ✅ {topic}: {coverage['confidence']:.0%} confidence")
        else:
            print(f"  ⭕ {topic}: Not yet covered")
    
    # Show context for LLM
    print("\n🤖 Context for LLM:")
    print("-" * 40)
    print(memory.get_context_for_llm())
    
    # Export full context
    print("\n\n📦 Exporting full context...")
    context_dict = memory.to_dict()
    with open("context_export.json", "w") as f:
        json.dump(context_dict, f, indent=2)
    print("✅ Exported to context_export.json")
    
    # Test scenario 5: Long conversation summarization
    print("\n\n5️⃣ Testing long conversation summarization...")
    print("-" * 40)
    
    # Add many messages to trigger summarization
    for i in range(10):
        memory.add_message(
            "patient", 
            f"I've been taking my medication regularly. Question {i+1}: Everything seems fine."
        )
    
    print("Added 10 more messages...")
    summary = memory.get_conversation_summary()
    print(f"\nUpdated Summary:\n{summary}")

if __name__ == "__main__":
    test_context_memory()
