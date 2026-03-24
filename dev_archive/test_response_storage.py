# test_response_storage.py
from response_storage import ResponseStorage, AnswerConfidence
import json
import time

def test_response_storage():
    """Test the response storage system"""
    
    print("\n" + "="*60)
    print("💾 Response Storage System Test")
    print("="*60)
    
    # Create storage
    storage = ResponseStorage()
    
    print(f"\n📞 Call ID: {storage.call_id}")
    
    # Simulate conversation
    print("\n1️⃣ Adding answers from conversation...")
    print("-" * 40)
    
    # Add answers with different confidence levels
    answers = [
        (1, "185 pounds", AnswerConfidence.HIGH, 0.95, "direct"),
        (2, "No side effects", AnswerConfidence.HIGH, 0.9, "direct"),
        (3, "Allergic to penicillin", AnswerConfidence.HIGH, 0.95, "direct"),
        (4, "Yes, every day", AnswerConfidence.HIGH, 0.9, "direct"),
        (5, "No new medications", AnswerConfidence.HIGH, 0.85, "direct"),
        (6, "No hospitalizations", AnswerConfidence.HIGH, 0.9, "direct"),
        (7, "Saw doctor last week", AnswerConfidence.HIGH, 0.85, "direct"),
        (8, "120 over 80", AnswerConfidence.HIGH, 0.95, "direct"),
        (9, "No new symptoms", AnswerConfidence.HIGH, 0.9, "direct"),
        (10, "Yes, need refill", AnswerConfidence.HIGH, 0.95, "direct"),
        (11, "Yes, working well", AnswerConfidence.HIGH, 0.9, "direct"),
        (12, "Appetite is normal", AnswerConfidence.MEDIUM, 0.7, "inferred"),
        (13, "Sleep is okay", AnswerConfidence.MEDIUM, 0.65, "inferred"),
        (14, "", AnswerConfidence.MISSING, 0.0, "none")  # Missing answer
    ]
    
    for q_id, answer, confidence, score, source in answers:
        if answer:
            storage.add_answer(q_id, answer, confidence, score, source)
            print(f"✓ Q{q_id}: {storage.answers[q_id].category} = '{answer}' ({confidence.value})")
    
    # Add conversation turns
    print("\n2️⃣ Adding conversation history...")
    print("-" * 40)
    
    conversation = [
        ("agent", "Hello, this is CareCaller. Am I speaking with John?"),
        ("patient", "Yes, this is John."),
        ("agent", "What is your current weight?"),
        ("patient", "185 pounds."),
        ("agent", "Have you experienced any side effects?"),
        ("patient", "No side effects."),
        ("agent", "Do you have any medication allergies?"),
        ("patient", "I'm allergic to penicillin."),
    ]
    
    for role, content in conversation:
        storage.add_conversation_turn(role, content)
        print(f"{role.upper()}: {content[:50]}...")
    
    # Show statistics
    print("\n3️⃣ Statistics:")
    print("-" * 40)
    
    answered = storage.get_answered_questions()
    missing = storage.get_missing_questions()
    
    print(f"Answered: {len(answered)}/14 questions")
    print(f"Missing: {len(missing)} questions")
    print(f"Completeness: {storage.get_completeness_score():.1%}")
    print(f"Quality Score: {storage.get_quality_score():.1%}")
    
    # Show issues
    print("\n4️⃣ Issues flagged:")
    print("-" * 40)
    issues = storage.flag_issues()
    for issue in issues:
        print(f"⚠️ {issue}")
    
    # Generate summary
    print("\n5️⃣ Summary:")
    print("-" * 40)
    summary = storage.generate_summary()
    print(json.dumps(summary, indent=2))
    
    # Export to JSON
    print("\n6️⃣ Exporting to JSON...")
    json_file = "test_call_output.json"
    storage.export_to_json(json_file)
    print(f"✅ Exported to {json_file}")
    
    # Export to CSV
    print("\n7️⃣ Exporting to CSV...")
    csv_file = "test_call_responses.csv"
    storage.export_to_csv(csv_file)
    print(f"✅ Exported to {csv_file}")
    
    # Validate against training format
    print("\n8️⃣ Validating against training format...")
    validation = storage.validate_against_training_format()
    if validation["valid"]:
        print("✅ Output matches training data format")
    else:
        print("❌ Validation issues found:")
        for field in validation.get("missing_fields", []):
            print(f"   Missing field: {field}")
    
    # Show final JSON preview
    print("\n9️⃣ JSON Preview:")
    print("-" * 40)
    record = storage.to_json()
    print(json.dumps({
        "call_id": record["call_id"],
        "outcome": record["outcome"],
        "response_completeness": record["response_completeness"],
        "responses_json": record["responses_json"][:3]  # First 3 responses
    }, indent=2))
    
    # Show uncertain answers
    print("\n🔟 Uncertain/Low Confidence Answers:")
    print("-" * 40)
    for answer in storage.uncertain_answers:
        print(f"⚠️ Q{answer.question_id} ({answer.category}): {answer.answer}")
        print(f"   Confidence: {answer.confidence_score:.0%} - {answer.validation_notes}")
    
    print("\n✅ Response storage test complete!")

if __name__ == "__main__":
    test_response_storage()
