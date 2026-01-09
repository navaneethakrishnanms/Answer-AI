"""
Comprehensive tests for Section and Evaluation Rules
"""

import pytest
from pathlib import Path
from tests.test_framework import test, time_test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rules.section_rules import SectionRules, QuestionParser
from app.rules.evaluation_rules import EvaluationRules
from unittest.mock import patch


class TestSectionRules:
    """Test suite for Section Rules"""
    
    @time_test
    @patch('app.rules.section_rules.Config')
    def test_get_section_config(self, mock_config):
        """Test section configuration retrieval"""
        mock_config.get.return_value = [
            {'name': 'A', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 10},
            {'name': 'B', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 20},
            {'name': 'C', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 20}
        ]
        
        config = SectionRules.get_section_config()
        
        assert 'A' in config
        assert 'B' in config
        assert 'C' in config
        assert config['A']['max_marks'] == 10
        assert config['B']['max_marks'] == 20
        assert config['C']['max_marks'] == 20
    
    @time_test
    @patch('app.rules.section_rules.Config')
    def test_validate_section_structure(self, mock_config):
        """Test section structure validation"""
        mock_config.get.return_value = [
            {'name': 'A', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 10}
        ]
        
        # Valid structure
        questions = [{'id': 'A1'}, {'id': 'A2'}, {'id': 'A3'}]
        is_valid, errors = SectionRules.validate_section_structure('A', questions)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid structure (wrong number of questions)
        questions = [{'id': 'A1'}, {'id': 'A2'}]
        is_valid, errors = SectionRules.validate_section_structure('A', questions)
        assert not is_valid
        assert len(errors) > 0
    
    @time_test
    @patch('app.rules.section_rules.Config')
    def test_should_drop_lowest(self, mock_config):
        """Test drop lowest logic"""
        mock_config.get.return_value = [
            {'name': 'A', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 10}
        ]
        
        # Should drop if answered all 3
        assert SectionRules.should_drop_lowest('A', 3) == True
        
        # Should not drop if answered only 2
        assert SectionRules.should_drop_lowest('A', 2) == False
        
        # Should not drop if answered only 1
        assert SectionRules.should_drop_lowest('A', 1) == False


class TestQuestionParser:
    """Test suite for Question Parser"""
    
    @time_test
    def test_parse_main_question_id(self):
        """Test main question ID parsing"""
        # Valid patterns
        assert QuestionParser.parse_main_question_id("A1") == ('A', '1')
        assert QuestionParser.parse_main_question_id("B2") == ('B', '2')
        assert QuestionParser.parse_main_question_id("C3") == ('C', '3')
        
        # Invalid patterns
        assert QuestionParser.parse_main_question_id("D1") == (None, None)
        assert QuestionParser.parse_main_question_id("A") == (None, None)
        assert QuestionParser.parse_main_question_id("1") == (None, None)
    
    @time_test
    def test_is_roman_subdivision(self):
        """Test roman numeral subdivision detection"""
        assert QuestionParser.is_roman_subdivision("(i)") == True
        assert QuestionParser.is_roman_subdivision("(ii)") == True
        assert QuestionParser.is_roman_subdivision("(iii)") == True
        assert QuestionParser.is_roman_subdivision("(iv)") == True
        assert QuestionParser.is_roman_subdivision("i") == True
        assert QuestionParser.is_roman_subdivision("(a)") == False
        assert QuestionParser.is_roman_subdivision("1") == False
    
    @time_test
    def test_is_alpha_subdivision(self):
        """Test alphabetic subdivision detection"""
        assert QuestionParser.is_alpha_subdivision("(a)") == True
        assert QuestionParser.is_alpha_subdivision("(b)") == True
        assert QuestionParser.is_alpha_subdivision("a") == True
        assert QuestionParser.is_alpha_subdivision("(i)") == False
        assert QuestionParser.is_alpha_subdivision("1") == False
    
    @time_test
    def test_is_numeric_subdivision(self):
        """Test numeric subdivision detection"""
        assert QuestionParser.is_numeric_subdivision("1") == True
        assert QuestionParser.is_numeric_subdivision("(2)") == True
        assert QuestionParser.is_numeric_subdivision("(3)") == True
        assert QuestionParser.is_numeric_subdivision("(a)") == False
        assert QuestionParser.is_numeric_subdivision("(i)") == False
    
    @time_test
    def test_extract_marks(self):
        """Test marks extraction from text"""
        test_cases = [
            ("Explain AI [5 marks]", 5, "Explain AI"),
            ("Define ML (3 marks)", 3, "Define ML"),
            ("Describe CNN [4m]", 4, "Describe CNN"),
            ("What is DL (2)", 2, "What is DL"),
            ("No marks here", None, "No marks here")
        ]
        
        for text, expected_marks, expected_text in test_cases:
            marks, clean_text = QuestionParser.extract_marks(text)
            assert marks == expected_marks
            if expected_marks is not None:
                assert clean_text.strip() == expected_text


class TestEvaluationRules:
    """Test suite for Evaluation Rules"""
    
    @time_test
    @patch('app.rules.evaluation_rules.Config')
    def test_is_one_mark_question(self, mock_config):
        """Test 1-mark question detection"""
        assert EvaluationRules.is_one_mark_question(1) == True
        assert EvaluationRules.is_one_mark_question(2) == False
        assert EvaluationRules.is_one_mark_question(0) == False
    
    @time_test
    def test_is_true_false_question(self):
        """Test True/False question detection"""
        test_cases = [
            ("State whether true or false", True),
            ("Mark True or False", True),
            ("True/False: AI is a subset of ML", True),
            ("T/F: Deep learning uses neural networks", True),
            ("Explain machine learning", False),
            ("What is AI?", False)
        ]
        
        for text, expected in test_cases:
            assert EvaluationRules.is_true_false_question(text) == expected
    
    @time_test
    @patch('app.rules.evaluation_rules.Config')
    def test_should_apply_strict_evaluation(self, mock_config):
        """Test strict evaluation rule detection"""
        mock_config.get.return_value = {
            'one_mark_questions': {'strict': True},
            'true_false': {'strict': True}
        }
        
        # 1-mark questions should be strict
        assert EvaluationRules.should_apply_strict_evaluation(1, "What is AI?") == True
        
        # True/False should be strict
        assert EvaluationRules.should_apply_strict_evaluation(2, "True or False: AI exists") == True
        
        # Multi-mark non-T/F should not be strict
        assert EvaluationRules.should_apply_strict_evaluation(5, "Explain AI") == False
    
    @time_test
    @patch('app.rules.evaluation_rules.Config')
    def test_should_apply_liberal_evaluation(self, mock_config):
        """Test liberal evaluation rule detection"""
        mock_config.get.return_value = {
            'multi_mark_questions': {'liberal': True}
        }
        
        # Multi-mark non-T/F should be liberal
        assert EvaluationRules.should_apply_liberal_evaluation(5, "Explain AI") == True
        
        # 1-mark should not be liberal
        assert EvaluationRules.should_apply_liberal_evaluation(1, "What is AI?") == False
        
        # True/False should not be liberal
        assert EvaluationRules.should_apply_liberal_evaluation(2, "True or False") == False
    
    @time_test
    def test_get_prompt_strings(self):
        """Test evaluation prompt string generation"""
        strict_prompt = EvaluationRules.get_strict_evaluation_prompt()
        liberal_prompt = EvaluationRules.get_liberal_evaluation_prompt()
        general_prompt = EvaluationRules.get_general_rules_prompt()
        
        assert "STRICT" in strict_prompt
        assert "LIBERAL" in liberal_prompt
        assert "NEVER penalize" in general_prompt
        assert len(strict_prompt) > 50
        assert len(liberal_prompt) > 50


# Register tests with framework
@test("rules_section_config", priority=6, category="rules")
def test_section_config():
    """Test section configuration"""
    print("  Testing section configuration...")
    with patch('app.rules.section_rules.Config') as mock:
        mock.get.return_value = [
            {'name': 'A', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 10}
        ]
        config = SectionRules.get_section_config()
        assert 'A' in config
    return True


@test("rules_question_parser", priority=6, category="rules")
def test_question_parser():
    """Test question parser"""
    print("  Testing question parser...")
    assert QuestionParser.parse_main_question_id("A1") == ('A', '1')
    assert QuestionParser.is_roman_subdivision("(i)") == True
    return True


@test("rules_evaluation", priority=5, dependencies=["rules_section_config"], category="rules")
def test_evaluation_rules():
    """Test evaluation rules"""
    print("  Testing evaluation rules...")
    assert EvaluationRules.is_one_mark_question(1) == True
    assert EvaluationRules.is_true_false_question("True or False") == True
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
