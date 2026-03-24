# test_validation.py
from validation_system import ValidationSystem, ValidationSeverity
import json

def test_validation():
    """Test the validation system with different scenarios"""
    
    print("\n" + "="*60)
    print("✅ Validation System Test")
    print("="*60)
    
    validator = ValidationSystem()
    
    # Test scenario 1: Good call
    print("\n1️⃣ Testing GOOD call...")
    print("-" * 40)
    
    good_call = {
        "call_id": "GOOD_CALL_001",
        "call_duration": 180,
        "transcript_text": """
[AGENT]: Hello, this is CareCaller. What is your current weight?
[USER]: 185 pounds
[AGENT]: Have you experienced any side effects?
[USER]: No side effects
[AGENT]: Do you have any medication allergies?
[USER]: No allergies
[AGENT]: Are you taking your medication as prescribed?
[USER]: Yes, every day
[AGENT]: Have you started any new medications?
[USER]: No
[AGENT]: Have you been hospitalized recently?
[USER]: No
[AGENT]: Have you seen your doctor recently?
[USER]: Yes, last month
[AGENT]: What is your blood pressure?
[USER]: 120 over 80
[AGENT]: Any new symptoms?
[USER]: No
[AGENT]: Do you need a refill?
[USER]: Yes
[AGENT]: Is your medication working?
[USER]: Yes
[AGENT]: How is your appetite?
[USER]: Normal
[AGENT]: How is your sleep?
[USER]: Good
[AGENT]: Any other concerns?
[USER]: No
""",
        "responses_json": [
            {"question": "Q1 Weight", "answer": "185 pounds"},
            {"question": "Q2 Side effects", "answer": "No"},
            {"question": "Q3 Allergies", "answer": "No"},
            {"question": "Q4 Medication taken", "answer": "Yes"},
            {"question": "Q5 New medications", "answer": "No"},
            {"question": "Q6 Hospitalization", "answer": "No"},
            {"question": "Q7 Doctor visit", "answer": "Yes, last month"},
            {"question": "Q8 Blood pressure", "answer": "120/80"},
            {"question": "Q9 Symptoms", "answer": "No"},
            {"question": "Q10 Refill", "answer": "Yes"},
            {"question": "Q11 Effectiveness", "answer": "Yes"},
            {"question": "Q12 Appetite", "answer": "Normal"},
            {"question": "Q13 Sleep", "answer": "Good"},
            {"question": "Q14 Concerns", "answer": "No"}
        ]
    }
    
    report = validator.validate_call(good_call)
    print(f"Score: {report.overall_score:.1f}/100")
    print(f"Valid: {report.is_valid}")
    print(f"Issues: {len(report.issues)}")
    print(f"Ticket needed: {report.ticket_needed}")
    
    # Test scenario 2: Problematic call
    print("\n\n2️⃣ Testing PROBLEMATIC call...")
    print("-" * 40)
    
    bad_call = {
        "call_id": "BAD_CALL_001",
        "call_duration": 45,
        "transcript_text": """
[AGENT]: Hello, what's your weight?
[USER]: I don't know
[AGENT]: You should take this medication twice a day
[USER]: Okay
[AGENT]: Have you had side effects?
[USER]: Maybe some nausea
[AGENT]: That's fine. Any allergies?
[USER]: Not sure
""",
        "responses_json": [
            {"question": "Q1 Weight", "answer": "I don't know"},
            {"question": "Q2 Side effects", "answer": "Maybe some nausea"},
            {"question": "Q3 Allergies", "answer": "Not sure"}
        ]
    }
    
    report = validator.validate_call(bad_call)
    print(f"Score: {report.overall_score:.1f}/100")
    print(f"Valid: {report.is_valid}")
    print(f"Issues: {len(report.issues)}")
    print(f"Ticket needed: {report.ticket_needed}")
    print(f"Ticket category: {report.ticket_category}")
    
    # Show issues
    print("\nIssues found:")
    for issue in report.issues:
        print(f"  [{issue.severity.value.upper()}] {issue.description}")
        if issue.recommendation:
            print(f"    → {issue.recommendation}")
    
    # Test scenario 3: Medical advice violation
    print("\n\n3️⃣ Testing MEDICAL ADVICE violation...")
    print("-" * 40)
    
    medical_advice_call = {
        "call_id": "MEDICAL_CALL_001",
        "call_duration": 120,
        "transcript_text": """
[AGENT]: Hello, this is CareCaller
[USER]: I have a headache
[AGENT]: You should take ibuprofen for that
[USER]: Okay, thanks
[AGENT]: Do you need a refill?
[USER]: Yes
""",
        "responses_json": [
            {"question": "Q1 Weight", "answer": "180"},
            {"question": "Q10 Refill", "answer": "Yes"}
        ]
    }
    
    report = validator.validate_call(medical_advice_call)
    print(f"Score: {report.overall_score:.1f}/100")
    print(f"Medical advice detected: {validator.metrics['agent_medical_advice_count']}")
    print(f"Ticket needed: {report.ticket_needed}")
    print(f"Ticket category: {report.ticket_category}")
    
    # Generate post-call summary
    print("\n\n4️⃣ Generating post-call summary...")
    print("-" * 40)
    summary = validator.generate_post_call_summary(report)
    print(summary)
    
    # Test scenario 4: Format validation
    print("\n\n5️⃣ Testing format validation...")
    print("-" * 40)
    
    format_call = {
        "call_id": "FORMAT_CALL_001",
        "call_duration": 90,
        "transcript_text": "",
        "responses_json": [
            {"question": "What is your weight?", "answer": "I think maybe around 180 something"},
            {"question": "What is your blood pressure?", "answer": "It's good"},
            {"question": "Do you have side effects?", "answer": "Sometimes"},
            {"question": "Any allergies?", "answer": "Yes to penicillin"},
        ]
    }
    
    report = validator.validate_call(format_call)
    print(f"Score: {report.overall_score:.1f}/100")
    print(f"Valid answers: {validator.metrics['questions_valid']}/{validator.metrics['questions_answered']}")
    
    # Export report
    print("\n\n6️⃣ Exporting validation report...")
    print("-" * 40)
    
    report_dict = report.to_dict()
    with open("validation_report.json", "w") as f:
        json.dump(report_dict, f, indent=2)
    print("✅ Exported to validation_report.json")
    
    print("\n" + "="*60)
    print("✅ Validation system test complete!")
    print("="*60)

if __name__ == "__main__":
    test_validation()
