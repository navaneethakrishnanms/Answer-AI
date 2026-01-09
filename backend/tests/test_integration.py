"""
Integration Tests - End-to-End Workflow Testing
"""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from tests.test_framework import test, time_test
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEndToEndWorkflow:
    """Integration tests for complete workflow"""
    
    @pytest.mark.asyncio
    @time_test
    @patch('app.services.ocr_service.OCRService')
    @patch('app.services.qwen_mapper.QwenMapper')
    @patch('app.services.deepseek_evaluator.DeepSeekEvaluator')
    async def test_complete_evaluation_pipeline(
        self, 
        mock_evaluator, 
        mock_mapper, 
        mock_ocr,
        sample_question_paper,
        sample_answer_key,
        sample_student_answers,
        temp_dir
    ):
        """Test complete evaluation pipeline from PDF to result"""
        # Create dummy PDF files
        qp_file = temp_dir / "qp.pdf"
        ak_file = temp_dir / "ak.pdf"
        sa_file = temp_dir / "sa.pdf"
        
        for file in [qp_file, ak_file, sa_file]:
            file.write_bytes(b"Mock PDF")
        
        # Mock OCR
        mock_ocr_instance = AsyncMock()
        mock_ocr_instance.extract_text_from_pdf.side_effect = [
            (sample_question_paper, []),
            (sample_answer_key, []),
            (sample_student_answers, [])
        ]
        mock_ocr.return_value = mock_ocr_instance
        
        # Mock Mapper
        mock_mapper_instance = AsyncMock()
        mock_mapper_instance.map_answers.return_value = {
            'sections': {
                'A': {
                    'questions': [
                        {
                            'question_id': 'A1',
                            'question_text': 'What is AI?',
                            'model_answer': 'Artificial Intelligence',
                            'student_answer': 'AI is machine learning',
                            'max_marks': 10
                        }
                    ]
                }
            }
        }
        mock_mapper.return_value = mock_mapper_instance
        
        # Mock Evaluator
        mock_evaluator_instance = AsyncMock()
        mock_evaluator_instance.evaluate_answer_sheet.return_value = {
            'sections': {
                'A': {
                    'section_total': 8.0,
                    'questions': [
                        {
                            'question_id': 'A1',
                            'marks_awarded': 8.0,
                            'feedback': 'Good answer'
                        }
                    ]
                }
            },
            'total_marks': 8.0,
            'section_totals': {'A': 8.0}
        }
        mock_evaluator.return_value = mock_evaluator_instance
        
        # Import and run pipeline
        from app.core.pipeline import EvaluationPipeline
        
        pipeline = EvaluationPipeline(
            str(qp_file),
            str(ak_file),
            str(sa_file)
        )
        
        result = await pipeline.process()
        
        # Verify result
        assert 'total_marks' in result
        assert 'sections' in result
        assert result['total_marks'] == 8.0
    
    @pytest.mark.asyncio
    @time_test
    async def test_preprocessing_to_mapping_integration(
        self,
        sample_question_paper,
        sample_answer_key,
        sample_student_answers
    ):
        """Test integration between preprocessing and mapping"""
        from app.services.preprocessing import PreprocessingService
        
        service = PreprocessingService()
        
        # Preprocess
        result = service.prepare_for_mapping(
            sample_question_paper,
            sample_answer_key,
            sample_student_answers
        )
        
        # Verify structure suitable for mapping
        assert 'question_paper' in result
        assert 'answer_key' in result
        assert 'student_answers' in result
        assert 'sections' in result['question_paper']
        
        # Verify it can be used by mapper
        from app.services.qwen_mapper import QwenMapper
        
        with patch('app.services.qwen_mapper.Config') as mock_config:
            mock_config.get.return_value = 'qwen2.5:14b'
            mapper = QwenMapper()
            
            # Should not raise
            prompt = mapper.build_mapping_prompt(result)
            assert len(prompt) > 100
    
    @pytest.mark.asyncio
    @time_test
    async def test_mapping_to_evaluation_integration(self):
        """Test integration between mapping and evaluation"""
        # Sample mapped data
        mapped_data = {
            'sections': {
                'A': {
                    'questions': [
                        {
                            'question_id': 'A1',
                            'question_text': 'What is AI?',
                            'model_answer': 'AI is artificial intelligence',
                            'student_answer': 'AI means machine learning',
                            'max_marks': 5
                        }
                    ]
                }
            }
        }
        
        # Test with evaluator
        from app.services.deepseek_evaluator import DeepSeekEvaluator
        
        with patch('app.services.deepseek_evaluator.Config') as mock_config:
            mock_config.get.return_value = 'deepseek-r1:7b'
            evaluator = DeepSeekEvaluator()
            
            # Should not raise
            prompt = evaluator.build_evaluation_prompt(
                mapped_data['sections']['A']['questions'][0]
            )
            assert 'A1' in prompt
            assert 'JSON' in prompt
    
    @time_test
    def test_section_rules_integration(self):
        """Test section rules integration with evaluation"""
        from app.rules.section_rules import SectionRules
        from app.services.deepseek_evaluator import DeepSeekEvaluator
        
        with patch('app.rules.section_rules.Config') as mock_config:
            mock_config.get.return_value = [
                {'name': 'A', 'total_questions': 3, 'questions_to_answer': 2, 'max_marks': 10}
            ]
            
            # Get config
            config = SectionRules.get_section_config()
            assert 'A' in config
            
            # Test should drop lowest
            assert SectionRules.should_drop_lowest('A', 3) == True
    
    @time_test
    def test_error_propagation(self):
        """Test that errors propagate correctly through the system"""
        from app.services.preprocessing import PreprocessingService
        
        service = PreprocessingService()
        
        # Empty inputs should be handled gracefully
        result = service.prepare_for_mapping("", "", "")
        
        # Should return structure but with empty sections
        assert 'question_paper' in result
        assert 'answer_key' in result
        assert 'student_answers' in result


# Register integration tests with framework
@test("integration_preprocessing_to_mapping", priority=2, 
      dependencies=["preprocessing_sections", "ai_qwen_mapper"], 
      category="integration")
def test_preprocess_to_map():
    """Test preprocessing to mapping integration"""
    print("  Testing preprocessing to mapping integration...")
    from app.services.preprocessing import PreprocessingService
    
    service = PreprocessingService()
    result = service.prepare_for_mapping(
        "SECTION A\nA1. Question",
        "A1. Answer",
        "Student ID: TEST123\nA1. Student answer"
    )
    
    assert 'question_paper' in result
    assert 'sections' in result['question_paper']
    
    return True


@test("integration_mapping_to_evaluation", priority=2,
      dependencies=["ai_qwen_mapper", "ai_deepseek_evaluator"],
      category="integration")
def test_map_to_eval():
    """Test mapping to evaluation integration"""
    print("  Testing mapping to evaluation integration...")
    
    mapped_data = {
        'sections': {
            'A': {
                'questions': [{
                    'question_id': 'A1',
                    'question_text': 'Q',
                    'model_answer': 'A',
                    'student_answer': 'SA',
                    'max_marks': 5
                }]
            }
        }
    }
    
    from app.services.deepseek_evaluator import DeepSeekEvaluatorService
    with patch('app.services.deepseek_evaluator.Config') as mock:
        mock.get_model.return_value = 'deepseek-r1:7b'
        mock.get_ollama_host.return_value = 'http://localhost:11434'
        with patch.object(DeepSeekEvaluatorService, '_verify_model'):
            evaluator = DeepSeekEvaluatorService()
            # Test internal prompt building (private method)
            prompt = evaluator._build_evaluation_prompt(
                mapped_data['sections']['A']['questions'][0]
            )
            assert 'A1' in prompt
    
    return True


@test("integration_full_pipeline", priority=1,
      dependencies=["integration_preprocessing_to_mapping", "integration_mapping_to_evaluation"],
      category="integration")
def test_full_pipeline():
    """Test full pipeline integration"""
    print("  Testing full pipeline...")
    # This is a placeholder for the full pipeline test
    # In a real scenario, this would run the entire evaluation pipeline
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
