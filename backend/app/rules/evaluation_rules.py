"""Evaluation rules for different question types"""

from typing import Dict
from app.config import Config

class EvaluationRules:
    """Rules for evaluating different types of questions"""
    
    @staticmethod
    def get_evaluation_config() -> Dict:
        """Get evaluation configuration from config.yaml"""
        return Config.get('exam_rules.evaluation', {})
    
    @staticmethod
    def is_one_mark_question(marks: int) -> bool:
        """Check if question is a 1-mark question"""
        return marks == 1
    
    @staticmethod
    def is_true_false_question(question_text: str) -> bool:
        """
        Check if question is True/False type
        
        Args:
            question_text: Question text
        
        Returns:
            True if it's a True/False question
        """
        text_lower = question_text.lower()
        indicators = [
            'true or false',
            'true/false',
            't/f',
            'state whether true or false',
            'mark true or false'
        ]
        
        return any(indicator in text_lower for indicator in indicators)
    
    @staticmethod
    def should_apply_strict_evaluation(marks: int, question_text: str) -> bool:
        """
        Determine if strict evaluation should be applied
        
        Args:
            marks: Marks for the question
            question_text: Question text
        
        Returns:
            True if strict evaluation should be applied
        """
        config = EvaluationRules.get_evaluation_config()
        
        # 1-mark questions are always strict
        if marks == 1 and config.get('one_mark_questions', {}).get('strict', True):
            return True
        
        # True/False questions are always strict
        if EvaluationRules.is_true_false_question(question_text):
            return config.get('true_false', {}).get('strict', True)
        
        return False
    
    @staticmethod
    def should_apply_liberal_evaluation(marks: int, question_text: str) -> bool:
        """
        Determine if liberal evaluation should be applied
        
        Args:
            marks: Marks for the question
            question_text: Question text
        
        Returns:
            True if liberal evaluation should be applied
        """
        config = EvaluationRules.get_evaluation_config()
        
        # Multi-mark questions get liberal evaluation
        if marks > 1 and not EvaluationRules.is_true_false_question(question_text):
            return config.get('multi_mark_questions', {}).get('liberal', True)
        
        return False
    
    @staticmethod
    def should_penalize_language(config: Dict = None) -> bool:
        """Check if language/grammar should be penalized"""
        if config is None:
            config = EvaluationRules.get_evaluation_config()
        
        penalties = config.get('penalties', {})
        return penalties.get('language_grammar', False)
    
    @staticmethod
    def should_penalize_spelling(config: Dict = None) -> bool:
        """Check if spelling should be penalized"""
        if config is None:
            config = EvaluationRules.get_evaluation_config()
        
        penalties = config.get('penalties', {})
        return penalties.get('spelling', False)
    
    @staticmethod
    def get_strict_evaluation_prompt() -> str:
        """Get prompt instructions for strict evaluation"""
        return """
STRICT EVALUATION MODE:
- Award FULL marks ONLY if the answer is completely correct
- Award ZERO marks if the answer is incorrect or partially correct
- NO partial marks allowed
- NO liberal interpretation
- For True/False: No marks for explanations, only the T/F answer matters
- Ignore spelling, grammar, and handwriting OCR errors
"""
    
    @staticmethod
    def get_liberal_evaluation_prompt() -> str:
        """Get prompt instructions for liberal evaluation"""
        return """
LIBERAL EVALUATION MODE:
- Evaluate based on CONCEPTS, not exact wording
- Award partial marks for partial understanding
- Accept different wording if the concept is correct
- Focus on core ideas, not peripheral details
- Ignore spelling, grammar, and handwriting OCR errors
- Penalize ONLY completely wrong concepts or missing core ideas
- Be FAIR and GENEROUS with marks
"""
    
    @staticmethod
    def get_general_rules_prompt() -> str:
        """Get general evaluation rules"""
        return """
GENERAL RULES:
- NEVER penalize for language, grammar, or spelling mistakes
- NEVER penalize for handwriting OCR noise or recognition errors
- Focus ONLY on the correctness of the concept/answer
- Be consistent across all questions
- Provide clear reasoning for marks awarded
"""
