# test_edge_cases.py
from edge_case_handler import EdgeCaseHandler, EdgeCaseType
import json

def test_edge_cases():
    """Test all edge case scenarios"""
    
    print("\n" + "="*60)
    print("🛡️ Edge Case Handler Test")
    print("="*60)
    
    handler = EdgeCaseHandler()
    
    # Test scenarios
    test_cases = [
        # Opt-out tests
        ("I don't want to continue this call", EdgeCaseType.OPT_OUT),
        ("Please stop calling me", EdgeCaseType.OPT_OUT),
        ("Opt out", EdgeCaseType.OPT_OUT),
        ("Not interested, thank you", EdgeCaseType.OPT_OUT),
        
        # Reschedule tests
        ("Can we reschedule for tomorrow?", EdgeCaseType.RESCHEDULE),
        ("I'm busy now, call back later", EdgeCaseType.RESCHEDULE),
        ("Not a good time, maybe in the evening", EdgeCaseType.RESCHEDULE),
        ("Call me back at 3pm", EdgeCaseType.RESCHEDULE),
        
        # Wrong number tests
        ("You have the wrong number", EdgeCaseType.WRONG_NUMBER),
        ("No one by that name lives here", EdgeCaseType.WRONG_NUMBER),
        ("This isn't John", EdgeCaseType.WRONG_NUMBER),
        
        # Medical advice tests
        ("Should I take this with food?", EdgeCaseType.MEDICAL_ADVICE),
        ("Is this medication safe?", EdgeCaseType.MEDICAL_ADVICE),
        ("What dosage should I take?", EdgeCaseType.MEDICAL_ADVICE),
        
        # Emergency tests
        ("I'm having chest pain", EdgeCaseType.EMERGENCY),
        ("I can't breathe", EdgeCaseType.EMERGENCY),
        ("This is a medical emergency", EdgeCaseType.EMERGENCY),
        
        # Pricing tests
        ("How much does this cost?", EdgeCaseType.PRICING),
        ("Is this covered by insurance?", EdgeCaseType.PRICING),
        ("What's the copay?", EdgeCaseType.PRICING),
        
        # Complaint tests
        ("I'm very unhappy with this service", EdgeCaseType.COMPLAINT),
        ("I want to speak to a manager", EdgeCaseType.COMPLAINT),
        ("This is unacceptable", EdgeCaseType.COMPLAINT),
        
        # Technical issue tests
        ("I can't hear you clearly", EdgeCaseType.TECHNICAL_ISSUE),
        ("The connection is breaking up", EdgeCaseType.TECHNICAL_ISSUE),
    ]
    
    print("\n📋 Testing detection accuracy:")
    print("-" * 40)
    
    correct = 0
    total = len(test_cases)
    
    for text, expected_type in test_cases:
        result = handler.detect_edge_case(text)
        
        if result:
            detected = result.case_type
            is_correct = detected == expected_type
            if is_correct:
                correct += 1
            
            status = "✅" if is_correct else "❌"
            print(f"\n{status} Input: {text[:50]}...")
            print(f"   Expected: {expected_type.value}")
            print(f"   Detected: {detected.value}")
            print(f"   Confidence: {result.confidence:.0%}")
            print(f"   Action: {result.action}")
            if result.extracted_data:
                print(f"   Data: {result.extracted_data}")
        else:
            print(f"\n⚠️ Input: {text[:50]}...")
            print(f"   Expected: {expected_type.value}")
            print(f"   Detected: None")
    
    print(f"\n\n📊 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    
    # Test specific handlers
    print("\n\n🔄 Testing specific handlers:")
    print("-" * 40)
    
    # Test reschedule handler
    print("\n1. Reschedule Handler:")
    reschedule_text = "Can we reschedule for Tuesday at 2pm?"
    result = handler.handle_reschedule(reschedule_text)
    print(f"   Input: {reschedule_text}")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test emergency handler
    print("\n2. Emergency Handler:")
    emergency_text = "I'm having chest pain"
    result = handler.handle_emergency(emergency_text)
    print(f"   Input: {emergency_text}")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test medical advice handler
    print("\n3. Medical Advice Handler:")
    advice_text = "Should I take this medication?"
    result = handler.handle_medical_advice(advice_text)
    print(f"   Input: {advice_text}")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test pricing handler
    print("\n4. Pricing Handler:")
    pricing_text = "How much does this cost?"
    result = handler.handle_pricing(pricing_text)
    print(f"   Input: {pricing_text}")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test priority system
    print("\n\n⚡ Priority System:")
    print("-" * 40)
    for case_type in EdgeCaseType:
        priority = handler.get_priority(case_type)
        print(f"   {case_type.value:20} → Priority: {priority}")
    
    # Test multiple detections in one call
    print("\n\n📞 Simulating full call with multiple edge cases:")
    print("-" * 40)
    
    handler.reset()
    
    call_scenario = [
        "Hello, is this John?",
        "Actually, how much does this cost?",  # Pricing
        "I understand. I need to reschedule for tomorrow",  # Reschedule
        "Also, I'm having some side effects, is that normal?"  # Medical advice
    ]
    
    for text in call_scenario:
        print(f"\n👤 Patient: {text}")
        result = handler.detect_edge_case(text)
        if result:
            print(f"🤖 Edge Case: {result.case_type.value}")
            print(f"   Response: {result.response}")
        else:
            print("🤖 No edge case detected")
    
    # Get summary
    summary = handler.get_edge_case_summary()
    print(f"\n\n📊 Call Summary:")
    print(json.dumps(summary, indent=2))
    
    # Test response safety
    print("\n\n🔒 Response Safety Validation:")
    print("-" * 40)
    
    safe_response = "Let me connect you with your doctor"
    unsafe_response = "You should take aspirin for that"
    
    print(f"Safe response: '{safe_response}'")
    print(f"  Valid: {handler.validate_response_safety(safe_response)}")
    print(f"Unsafe response: '{unsafe_response}'")
    print(f"  Valid: {handler.validate_response_safety(unsafe_response)}")

if __name__ == "__main__":
    test_edge_cases()
