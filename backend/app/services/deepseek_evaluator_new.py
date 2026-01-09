"""DeepSeek-R1 Evaluation Service - EVALUATION ONLY (Optimized)"""

import json
import logging
import re
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from app.config import Config
from app.schemas.mapping_schema import MappingOutputSchema
from app.schemas.evaluation_schema import (
    EvaluationOutputSchema,
    SectionEvaluationSchema,
    QuestionEvaluationSchema,
    EvaluationValidationSchema
)
from app.rules import SectionRules
from app.logger import get_job_logger

logger = logging.getLogger(__name__)

class DeepSeekEvaluatorService:
    """Service for evaluating student answers using DeepSeek-R1 with retry logic"""
    
    def __init__(self):
        self.host = Config.get_ollama_host()
        self.model = Config.get_model('evaluation')
        self.temperature = 0.1  # Low for consistency
        self.timeout = None  # No timeout - allow unlimited time
        self.max_retries = 3
        self.retry_delay = 3  # Faster retry
        
        logger.info(f"DeepSeek Evaluator initialized: {self.model} (no timeout)")
    
    async def _check_model_availability(self) -> bool:
        """Check if model is available"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.host}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    available = any(m['name'] == self.model for m in models)
                    if not available:
                        logger.warning(f"Model {self.model} not found!")
                    return available
        except Exception as e:
            logger.error(f"Model check failed: {str(e)}")
        return False
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict]:
        """Extract JSON with multiple fallback strategies"""
        if not text or not text.strip():
            return None
        
        # Remove thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = text.strip()
        
        # Try markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try finding JSON object
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Try parsing entire text
        try:
            return json.loads(text)
        except:
            pass
        
        return None
    
    def _build_evaluation_prompt(self, section_id: str, mapping_data: MappingOutputSchema) -> str:
        """Build simplified evaluation prompt"""
        section = mapping_data.sections.get(section_id)
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        student_answers = mapping_data.student_answers.get(section_id, [])
        answer_key = mapping_data.answer_key.get(section_id, [])
        questions = section.questions
        max_marks = section.max_marks
        
        prompt = f"""Evaluate Section {section_id} student answers. Return ONLY valid JSON.

**RULES:**
1. 1-mark questions: STRICT (full or zero, no partial)
2. Multi-mark questions: LIBERAL (partial marks OK)
3. Ignore spelling/grammar errors
4. Focus on concepts, not exact wording

**Section {section_id} ({max_marks} marks total)**

**Questions:**
"""
        
        for q in questions:
            # Find model answer
            model_ans = "Not provided"
            for ak in answer_key:
                if ak.question_ref == q.question_id:
                    model_ans = ak.expected_answer
                    break
            
            # Find student answer
            student_ans = "Not answered"
            for sa in student_answers:
                if sa.question_ref == q.question_id:
                    student_ans = sa.answer_text
                    break
            
            prompt += f"""
**Q{q.question_id} [{q.marks or 0}m]:** {q.content or 'N/A'}
Model: {model_ans}
Student: {student_ans}
"""
        
        prompt += f"""
**OUTPUT (JSON ONLY, NO MARKDOWN):**
{{
  "section_id": "{section_id}",
  "questions_evaluated": [
    {{
      "question_ref": "{questions[0].question_id if questions else section_id+'1'}",
      "marks_obtained": 0.0,
      "max_marks": {questions[0].marks if questions and questions[0].marks else 0},
      "reasoning": "Brief reasoning",
      "feedback": "Brief feedback",
      "subdivisions": null,
      "evaluated": true,
      "dropped": false
    }}
  ],
  "total_marks_obtained": 0.0,
  "max_marks": {max_marks},
  "questions_answered": {len(questions)},
  "dropped_question": null,
  "remarks": "Section summary"
}}
"""
        return prompt
    
    async def _call_ollama_with_retry(self, prompt: str, job_id: Optional[str] = None) -> str:
        """Call Ollama with retry logic"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        for attempt in range(self.max_retries):
            try:
                job_logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(None, connect=30.0)) as client:
                    response = await client.post(
                        f"{self.host}/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": "You are an exam evaluator. Return ONLY valid JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            "stream": False,
                            "options": {
                                "temperature": 0.05,
                                "top_p": 0.9,
                                "num_predict": 4096,
                                "stop": ["</think>", "</thinking>"],
                                "num_ctx": 8192
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        content = response.json().get('message', {}).get('content', '').strip()
                        if content:
                            job_logger.info(f"✓ Got response ({len(content)} chars)")
                            return content
                        job_logger.warning("Empty response")
                    else:
                        job_logger.error(f"HTTP {response.status_code}")
                
            except httpx.TimeoutException:
                job_logger.warning(f"Timeout (attempt {attempt + 1})")
            except Exception as e:
                job_logger.error(f"Error: {str(e)}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        raise Exception(f"Failed after {self.max_retries} attempts")
    
    async def evaluate_section(
        self,
        section_id: str,
        mapping_data: MappingOutputSchema,
        job_id: Optional[str] = None
    ) -> SectionEvaluationSchema:
        """Evaluate a single section"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        try:
            job_logger.info(f"Evaluating section {section_id}")
            
            # Build prompt
            prompt = self._build_evaluation_prompt(section_id, mapping_data)
            
            # Call model with retry
            response_text = await self._call_ollama_with_retry(prompt, job_id)
            
            # Extract JSON
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                job_logger.error("Failed to parse JSON")
                job_logger.error(f"Response: {response_text[:500]}")
                raise ValueError("Invalid JSON from model")
            
            # Parse into schema
            section_eval = SectionEvaluationSchema(**json_data)
            job_logger.info(f"✓ Section {section_id}: {section_eval.total_marks_obtained}/{section_eval.max_marks}")
            
            return section_eval
            
        except Exception as e:
            job_logger.error(f"Error: {str(e)}")
            raise
    
    async def evaluate_exam(
        self,
        mapping_data: MappingOutputSchema,
        job_id: Optional[str] = None
    ) -> EvaluationOutputSchema:
        """Evaluate complete exam (parallel evaluation for speed)"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        # Check model
        if not await self._check_model_availability():
            raise Exception(f"Model {self.model} not available")
        
        sections_to_evaluate = list(mapping_data.sections.keys())
        job_logger.info(f"Evaluating sections: {sections_to_evaluate}")
        
        # Evaluate all sections in parallel (2x faster)
        tasks = []
        for section_id in sections_to_evaluate:
            task = self.evaluate_section(section_id, mapping_data, job_id)
            tasks.append((section_id, task))
        
        # Wait for all
        section_results = {}
        for section_id, task in tasks:
            try:
                result = await task
                section_results[section_id] = result
            except Exception as e:
                job_logger.error(f"Section {section_id} failed: {str(e)}")
                # Create empty result
                section = mapping_data.sections[section_id]
                section_results[section_id] = SectionEvaluationSchema(
                    section_id=section_id,
                    questions_evaluated=[],
                    total_marks_obtained=0.0,
                    max_marks=section.max_marks,
                    questions_answered=0,
                    dropped_question=None,
                    remarks="Evaluation failed"
                )
        
        # Calculate totals
        total_marks = sum(s.total_marks_obtained for s in section_results.values())
        max_possible = sum(s.max_marks for s in section_results.values())
        percentage = (total_marks / max_possible * 100) if max_possible > 0 else 0
        
        # Generate remarks
        if percentage >= 90:
            remarks = "Outstanding!"
        elif percentage >= 75:
            remarks = "Excellent work!"
        elif percentage >= 60:
            remarks = "Good effort!"
        elif percentage >= 50:
            remarks = "Satisfactory."
        else:
            remarks = "Needs improvement."
        
        result = EvaluationOutputSchema(
            student_id=mapping_data.student_id,
            sections=section_results,
            total_marks=total_marks,
            max_total_marks=max_possible,
            percentage=round(percentage, 2),
            remarks=remarks,
            evaluation_metadata={
                'model': self.model,
                'sections_evaluated': len(section_results)
            }
        )
        
        job_logger.info(f"✓ Completed: {total_marks}/{max_possible} ({percentage:.1f}%)")
        return result
    
    def validate_evaluation(self, evaluation: EvaluationOutputSchema) -> EvaluationValidationSchema:
        """Validate evaluation (non-blocking)"""
        warnings = []
        
        if evaluation.total_marks > evaluation.max_total_marks:
            warnings.append(f"Total {evaluation.total_marks} > max {evaluation.max_total_marks}")
        
        expected_pct = (evaluation.total_marks / evaluation.max_total_marks * 100) if evaluation.max_total_marks > 0 else 0
        if abs(evaluation.percentage - expected_pct) > 0.1:
            warnings.append(f"Percentage mismatch: {evaluation.percentage} vs {expected_pct:.2f}")
        
        existing_sections = list(evaluation.sections.keys())
        
        return EvaluationValidationSchema(
            is_valid=len(warnings) == 0,
            errors=[],
            warnings=warnings,
            marks_within_limits=evaluation.total_marks <= evaluation.max_total_marks,
            section_a_valid='A' in existing_sections,
            section_b_valid='B' in existing_sections,
            section_c_valid='C' in existing_sections
        )
