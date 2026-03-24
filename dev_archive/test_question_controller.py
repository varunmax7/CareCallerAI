# test_question_controller.py
from question_controller import QuestionFlowController
import json

def test_question_flow():
    """Test the question flow controller with various scenarios"""
    
    print("\n" + "="*60)
    print("📋 Question Flow Controller Test")
    print("="*60)
    
    controller = QuestionFlowController()
    
    # Test scenario 1: Normal flow
    print("\n1️⃣ Testing normal flow...")
    print("-" * 40)
    
    while True:
        next_q = controller.get_next_question()
        if not next_q:
            print("✅ All questions completed!")
            break
        
        print(f"\n🤖 Q{next_q.id} ({next_q.category}): {next_q.question_text}")
        
        # Simulate answers
        if next_q.category == "weight":
            answer = "185 pounds"
        elif next_q.category == "side_effects":
            answer = "no"
        elif next_q.category == "allergies":
            answer = "no"
        elif next_q.category == "medication_taken":
            answer = "yes"
        elif next_q.category == "new_medications":
            answer = "no"
        elif next_q.category == "hospitalization":
            answer = "no"
        elif next_q.category == "doctor_visit":
            answer = "yes, last month"
        elif next_q.category == "blood_pressure":
            answer = "120 over 80"
        elif next_q.category == "symptoms":
            answer = "no"
        elif next_q.category == "refill_timing":
            answer = "yes"
        elif next_q.category == "medication_effectiveness":
            answer = "yes"
        elif next_q.category == "appetite":
            answer = "normal"
        elif next_q.category == "sleep":
            answer = "good"
        else:
            answer = "no"
        
        print(f"👤 Patient: {answer}")
        result = controller.process_answer(next_q.id, answer)
        print(f"🤖 Status: {result['status']}")
        
        if result['status'] == 'reask':
            print(f"🤖 Please: {result['message']}")
            # Simulate re-ask with better answer
            if "number" in result['message']:
                result = controller.process_answer(next_q.id, "185")
    
    # Show progress
    print("\n" + "="*60)
    print("📊 Final Progress")
    print("="*60)
    progress = controller.get_progress()
    print(json.dumps(progress, indent=2))
    
    # Test scenario 2: Skip logic with side effects
    print("\n\n2️⃣ Testing skip logic...")
    print("-" * 40)
    
    controller.reset()
    print("Question: Have you experienced any side effects?")
    answer = "yes, some nausea"
    print(f"Patient: {answer}")
    result = controller.process_answer(2, answer)
    print(f"Result: {result['status']}")
    
    # Check if follow-up was added
    next_q = controller.get_next_question()
    if next_q and next_q.id > 100:
        print(f"✓ Follow-up added: {next_q.question_text}")
    
    # Test scenario 3: Invalid answer handling
    print("\n\n3️⃣ Testing invalid answer handling...")
    print("-" * 40)
    
    controller.reset()
    print("Question: What is your weight?")
    answer = "I don't know"
    print(f"Patient: {answer}")
    
    for attempt in range(3):
        result = controller.process_answer(1, answer)
        print(f"Attempt {attempt + 1}: {result['status']} - {result.get('message', '')}")
        
        if result['status'] == 'invalid':
            answer = "around 180"  # Better answer on next attempt
        elif result['status'] == 'reask':
            answer = "185 pounds"  # Clear answer
    
    # Test scenario 4: Edge cases
    print("\n\n4️⃣ Testing edge cases...")
    print("-" * 40)
    
    controller.reset()
    
    # Test blood pressure validation
    print("\nBlood Pressure Question:")
    bp_tests = [
        ("120 over 80", "valid"),
        ("150/95", "valid"),
        ("I think it's normal", "unclear"),
        ("200/150", "invalid - out of range")
    ]
    
    for test_answer, expected in bp_tests:
        print(f"  Answer: '{test_answer}' -> Expected: {expected}")
        result = controller.process_answer(8, test_answer)
        print(f"    Result: {result['status']}")
    
    # Test weight validation
    print("\nWeight Question:")
    weight_tests = [
        ("185 pounds", "valid"),
        ("62", "invalid - too low"),
        ("350", "valid"),
        ("500", "valid"),
        ("600", "invalid - too high")
    ]
    
    for test_answer, expected in weight_tests:
        print(f"  Answer: '{test_answer}' -> Expected: {expected}")
        result = controller.process_answer(1, test_answer)
        print(f"    Result: {result['status']}")

if __name__ == "__main__":
    test_question_flow()
