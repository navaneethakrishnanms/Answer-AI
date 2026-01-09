"""
Test script to verify Qwen mapping JSON output
Run this to test mapping without going through the full pipeline
"""

import asyncio
import json
from pathlib import Path
from app.services.preprocessing import PreprocessingService
from app.services.qwen_mapper import QwenMapperService

async def test_mapping():
    print("="*60)
    print("TESTING QWEN MAPPING SERVICE")
    print("="*60)
    
    # Sample test data
    test_data = {
        'question_paper': {
            'full_text': '''
SECTION A
A1. What is Python? (5 marks)
A2. Define OOP. (5 marks)

SECTION B
B1. True or False: Python is compiled language (1 mark)
B2. Explain inheritance (4 marks)
''',
            'sections': {
                'A': 'SECTION A\nA1. What is Python? (5 marks)\nA2. Define OOP. (5 marks)',
                'B': 'SECTION B\nB1. True or False: Python is compiled language (1 mark)\nB2. Explain inheritance (4 marks)'
            }
        },
        'answer_key': {
            'full_text': '''
SECTION A
A1. Python is a high-level programming language
A2. OOP means Object Oriented Programming

SECTION B
B1. False
B2. Inheritance is a mechanism to reuse code
'''
        },
        'student_answers': {
            'full_text': '''
SECTION A
A1. Python is programming language for coding
A2. OOP is object oriented programming concept

SECTION B
B1. False
B2. Inheritance means child class inherits from parent
''',
            'student_id': 'TEST123'
        },
        'metadata': {
            'qp_length': 200,
            'ak_length': 150,
            'sa_length': 180,
            'sections_found': ['A', 'B']
        }
    }
    
    print("\n📝 Test Data Prepared")
    print(f"   Sections: {test_data['metadata']['sections_found']}")
    
    try:
        print("\n🤖 Initializing Qwen Mapper...")
        mapper = QwenMapperService()
        
        print("🚀 Starting mapping (this may take 30-60 seconds)...")
        print("   Please wait...")
        
        result = await mapper.map_exam_data(test_data)
        
        print("\n✅ MAPPING SUCCESSFUL!")
        print("="*60)
        print("\n📊 Mapping Results:")
        print(f"   Sections mapped: {list(result.sections.keys())}")
        
        for section_id, section in result.sections.items():
            print(f"\n   Section {section_id}:")
            print(f"      Questions: {len(section.questions)}")
            print(f"      Max marks: {section.max_marks}")
        
        print(f"\n   Student answers found:")
        for section_id, answers in result.student_answers.items():
            print(f"      Section {section_id}: {len(answers)} answers")
        
        print(f"\n   Answer key entries:")
        for section_id, answers in result.answer_key.items():
            print(f"      Section {section_id}: {len(answers)} entries")
        
        # Validate
        print("\n🔍 Validating mapping...")
        validation = mapper.validate_mapping(result)
        
        if validation.is_valid:
            print("   ✅ Validation PASSED")
        else:
            print("   ❌ Validation FAILED")
            if validation.errors:
                print(f"   Errors: {validation.errors}")
            if validation.warnings:
                print(f"   Warnings: {validation.warnings}")
        
        # Show JSON structure
        print("\n📄 JSON Output (first 500 chars):")
        json_output = result.model_dump_json(indent=2)
        print(json_output[:500])
        print("...")
        
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("QWEN MAPPING SERVICE TEST")
    print("="*60)
    print("\nThis script tests the Qwen mapping service")
    print("to ensure it produces valid JSON output.")
    print("\nMake sure:")
    print("  1. Backend dependencies are installed")
    print("  2. Ollama is running")
    print("  3. qwen2.5:14b model is available")
    print("\n" + "="*60)
    
    success = asyncio.run(test_mapping())
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Tests failed!")
        exit(1)
