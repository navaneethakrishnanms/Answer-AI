"""
Comprehensive tests for AI Services (Qwen Mapper and DeepSeek Evaluator)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from tests.test_framework import test, time_test
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.qwen_mapper import QwenMapperService
from app.services.deepseek_evaluator import DeepSeekEvaluatorService


class TestQwenMapper:
    """Test suite for Qwen Mapper Service"""
    
    @pytest.fixture
    def qwen_mapper(self):
        """Create Qwen mapper instance"""
        with patch('app.services.qwen_mapper.Config') as mock_config:
            mock_config.get_ollama_host.return_value = 'http://localhost:11434'
            mock_config.get_model.return_value = 'qwen2.5:14b'
            mock_config.get.side_effect = lambda key, default=None: {
                'ollama.temperature.mapping': 0.1,
                'ollama.timeout': 120
            }.get(key, default)
            with patch.object(QwenMapperService, '_verify_model'):
                return QwenMapperService()
    
    @time_test
    def test_mapper_initialization(self, qwen_mapper):
        """Test Qwen mapper initialization"""
        assert qwen_mapper is not None
        assert qwen_mapper.model == 'qwen2.5:14b'
        assert qwen_mapper.temperature == 0.1
    
    @time_test
    def test_build_mapping_prompt(self, qwen_mapper):
        """Test mapping prompt generation"""
        preprocessed_data = {
            'question_paper': {
                'sections': {
                    'A': 'Question A1\nQuestion A2'
                }
            },
            'answer_key': {
                'sections': {
                    'A': 'Answer to A1\nAnswer to A2'
                }
            },
            'student_answers': {
                'student_id': 'TEST001',
                'sections': {
                    'A': 'Student answer to A1\nStudent answer to A2'
                }
            }
        }
        
        prompt = qwen_mapper.build_mapping_prompt(preprocessed_data)
        
        assert 'Question Paper' in prompt
        assert 'Answer Key' in prompt
        assert 'Student Answers' in prompt
        assert 'TEST001' in prompt
        assert 'JSON' in prompt
        assert 'SECTION' in prompt
    
    @pytest.mark.asyncio
    @time_test
    @patch('aiohttp.ClientSession')
    async def test_map_answers_success(self, mock_session, qwen_mapper):
        """Test successful answer mapping"""
        # Mock Ollama response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'response': json.dumps({
                'sections': {
                    'A': {
                        'questions': [
                            {
                                'question_id': 'A1',
                                'question_text': 'What is AI?',
                                'model_answer': 'AI is artificial intelligence',
                                'student_answer': 'AI is machine learning',
                                'max_marks': 5
                            }
                        ]
                    }
                }
            })
        })
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        preprocessed_data = {
            'question_paper': {'sections': {'A': 'Q1'}},
            'answer_key': {'sections': {'A': 'A1'}},
            'student_answers': {'student_id': 'TEST', 'sections': {'A': 'SA1'}}
        }
        
        result = await qwen_mapper.map_answers(preprocessed_data)
        
        assert 'sections' in result
        assert 'A' in result['sections']
        assert 'questions' in result['sections']['A']
    
    @pytest.mark.asyncio
    @time_test
    @patch('aiohttp.ClientSession')
    async def test_map_answers_timeout(self, mock_session, qwen_mapper):
        """Test mapping timeout handling"""
        import asyncio
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.side_effect = asyncio.TimeoutError()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        preprocessed_data = {
            'question_paper': {'sections': {}},
            'answer_key': {'sections': {}},
            'student_answers': {'student_id': 'TEST', 'sections': {}}
        }
        
        with pytest.raises(Exception):
            await qwen_mapper.map_answers(preprocessed_data)
    
    @time_test
    def test_validate_mapping_output(self, qwen_mapper):
        """Test mapping output validation"""
        # Valid output
        valid_output = {
            'sections': {
                'A': {
                    'questions': [
                        {
                            'question_id': 'A1',
                            'question_text': 'Q',
                            'model_answer': 'A',
                            'student_answer': 'SA',
                            'max_marks': 5
                        }
                    ]
                }
            }
        }
        
        # Should not raise
        qwen_mapper.validate_mapping_output(valid_output)
        
        # Invalid output (missing sections)
        invalid_output = {'data': 'wrong structure'}
        
        with pytest.raises(Exception):
            qwen_mapper.validate_mapping_output(invalid_output)


class TestDeepSeekEvaluator:
    """Test suite for DeepSeek Evaluator Service"""
    
    @pytest.fixture
    def deepseek_evaluator(self):
        """Create DeepSeek evaluator instance"""
        with patch('app.services.deepseek_evaluator.Config') as mock_config:
            mock_config.get_ollama_host.return_value = 'http://localhost:11434'
            mock_config.get_model.return_value = 'deepseek-r1:7b'
            mock_config.get.side_effect = lambda key, default=None: {
                'ollama.temperature.evaluation': 0.3,
                'ollama.timeout': 120
            }.get(key, default)
            with patch.object(DeepSeekEvaluatorService, '_verify_model'):
                return DeepSeekEvaluatorService()
    
    @time_test
    def test_evaluator_initialization(self, deepseek_evaluator):
        """Test DeepSeek evaluator initialization"""
        assert deepseek_evaluator is not None
        assert deepseek_evaluator.model == 'deepseek-r1:7b'
        assert deepseek_evaluator.temperature == 0.3
    
    @time_test
    def test_build_evaluation_prompt_strict(self, deepseek_evaluator):
        """Test evaluation prompt for strict questions"""
        question_data = {
            'question_id': 'A1',
            'question_text': 'What is AI?',
            'model_answer': 'Artificial Intelligence',
            'student_answer': 'Machine Learning',
            'max_marks': 1
        }
        
        prompt = deepseek_evaluator.build_evaluation_prompt(question_data)
        
        assert 'STRICT' in prompt
        assert 'A1' in prompt
        assert 'Artificial Intelligence' in prompt
        assert 'Machine Learning' in prompt
        assert 'JSON' in prompt
    
    @time_test
    def test_build_evaluation_prompt_liberal(self, deepseek_evaluator):
        """Test evaluation prompt for liberal questions"""
        question_data = {
            'question_id': 'B1',
            'question_text': 'Explain deep learning',
            'model_answer': 'Deep learning is a subset of ML...',
            'student_answer': 'Deep learning uses neural networks...',
            'max_marks': 10
        }
        
        prompt = deepseek_evaluator.build_evaluation_prompt(question_data)
        
        assert 'LIBERAL' in prompt
        assert 'B1' in prompt
        assert 'JSON' in prompt
    
    @pytest.mark.asyncio
    @time_test
    @patch('aiohttp.ClientSession')
    async def test_evaluate_single_question_success(self, mock_session, deepseek_evaluator):
        """Test successful single question evaluation"""
        # Mock Ollama response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'response': json.dumps({
                'marks_awarded': 8.0,
                'feedback': 'Good answer with minor gaps',
                'evaluation_type': 'liberal'
            })
        })
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        question_data = {
            'question_id': 'B1',
            'question_text': 'Explain AI',
            'model_answer': 'AI is...',
            'student_answer': 'AI means...',
            'max_marks': 10
        }
        
        result = await deepseek_evaluator.evaluate_single_question(question_data)
        
        assert 'marks_awarded' in result
        assert 'feedback' in result
        assert result['marks_awarded'] == 8.0
    
    @pytest.mark.asyncio
    @time_test
    @patch('aiohttp.ClientSession')
    async def test_evaluate_answer_sheet_success(self, mock_session, deepseek_evaluator):
        """Test full answer sheet evaluation"""
        # Mock Ollama response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'response': json.dumps({
                'marks_awarded': 7.5,
                'feedback': 'Good answer',
                'evaluation_type': 'liberal'
            })
        })
        
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        mapped_data = {
            'sections': {
                'A': {
                    'questions': [
                        {
                            'question_id': 'A1',
                            'question_text': 'Q1',
                            'model_answer': 'A1',
                            'student_answer': 'SA1',
                            'max_marks': 10
                        },
                        {
                            'question_id': 'A2',
                            'question_text': 'Q2',
                            'model_answer': 'A2',
                            'student_answer': 'SA2',
                            'max_marks': 10
                        }
                    ]
                }
            }
        }
        
        result = await deepseek_evaluator.evaluate_answer_sheet(mapped_data)
        
        assert 'sections' in result
        assert 'A' in result['sections']
        assert 'total_marks' in result
        assert 'section_totals' in result
    
    @time_test
    def test_apply_section_rules_drop_lowest(self, deepseek_evaluator):
        """Test section rules with drop lowest"""
        with patch('app.services.deepseek_evaluator.SectionRules') as mock_rules:
            mock_rules.should_drop_lowest.return_value = True
            mock_rules.get_section_config.return_value = {
                'A': {'total_questions': 3, 'questions_to_answer': 2}
            }
            
            questions = [
                {'marks_awarded': 5.0, 'max_marks': 10},
                {'marks_awarded': 8.0, 'max_marks': 10},
                {'marks_awarded': 3.0, 'max_marks': 10}
            ]
            
            result = deepseek_evaluator.apply_section_rules('A', questions)
            
            # Should drop the lowest (3.0)
            assert result['section_total'] == 13.0  # 5 + 8


# Register tests with framework
@test("ai_qwen_mapper", priority=4, dependencies=["preprocessing_sections"], category="ai")
def test_qwen():
    """Test Qwen mapper"""
    print("  Testing Qwen mapper...")
    with patch('app.services.qwen_mapper.Config') as mock:
        mock.get_model.return_value = 'qwen2.5:14b'
        mock.get_ollama_host.return_value = 'http://localhost:11434'
        with patch.object(QwenMapperService, '_verify_model'):
            mapper = QwenMapperService()
            assert mapper.model == 'qwen2.5:14b'
    return True


@test("ai_deepseek_evaluator", priority=4, dependencies=["rules_evaluation"], category="ai")
def test_deepseek():
    """Test DeepSeek evaluator"""
    print("  Testing DeepSeek evaluator...")
    with patch('app.services.deepseek_evaluator.Config') as mock:
        mock.get_model.return_value = 'deepseek-r1:7b'
        mock.get_ollama_host.return_value = 'http://localhost:11434'
        with patch.object(DeepSeekEvaluatorService, '_verify_model'):
            evaluator = DeepSeekEvaluatorService()
            assert evaluator.model == 'deepseek-r1:7b'
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
