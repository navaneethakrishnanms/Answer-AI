"""DeepSeek-R1 Evaluation Service - Per-Question Evaluation (Optimized)"""

import json
import logging
import re
import asyncio
import random
import httpx
from typing import Dict, Any, List, Optional
from app.config import Config
from app.schemas.mapping_schema import MappingOutputSchema, PartSchema, QuestionSchema
from app.schemas.evaluation_schema import (
    EvaluationOutputSchema,
    SectionEvaluationSchema,
    PartEvaluationSchema,
    QuestionEvaluationSchema,
    EvaluationValidationSchema
)
from app.rules import SectionRules
from app.logger import get_job_logger

logger = logging.getLogger(__name__)


class DeepSeekEvaluatorService:
    """
    Service for evaluating student answers using DeepSeek-R1.
    Uses per-question evaluation for speed and reliability.
    """
    
    def __init__(self):
        self.host = Config.get_ollama_host()
        self.model = Config.get_model('evaluation')
        self.temperature = 0.05  # Very low for consistency
        self.max_retries = 3
        self.base_retry_delay = 2  # Base delay in seconds
        
        logger.info(f"DeepSeek Evaluator initialized: {self.model}")
    
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
    
    def _build_question_prompt(
        self, 
        question: QuestionSchema, 
        student_answer: str, 
        expected_answer: str,
        keywords: Optional[List[str]] = None
    ) -> str:
        """Build a prompt for evaluating a single question"""
        
        question_type = question.question_type or "multi-mark"
        marks = question.marks
        
        # Determine evaluation mode
        if marks == 1 or question_type == "1-mark":
            eval_mode = "STRICT: Full marks or zero. No partial."
        elif question_type == "true-false":
            eval_mode = "STRICT: Only T/F matters. Ignore explanation."
        else:
            eval_mode = "LIBERAL: Partial marks OK. Focus on concepts."
        
        keywords_hint = ""
        if keywords:
            keywords_hint = f"\nKey concepts to look for: {', '.join(keywords)}"
        
        prompt = f"""Evaluate this answer. Return ONLY JSON.

**Question ({marks} marks):** {question.content or 'N/A'}
**Expected Answer:** {expected_answer}{keywords_hint}
**Student Answer:** {student_answer}

**Evaluation Mode:** {eval_mode}

**RULES:**
- Ignore spelling/grammar errors
- Focus on conceptual correctness
- {eval_mode}

**OUTPUT (JSON ONLY):**
{{
  "question_ref": "{question.question_id}",
  "marks_obtained": <0 to {marks}>,
  "max_marks": {marks},
  "reasoning": "Brief reason for marks",
  "feedback": "Helpful feedback for student",
  "question_type": "{question_type}",
  "evaluated": true
}}
"""
        return prompt
    
    async def _call_ollama_with_retry(
        self, 
        prompt: str, 
        job_id: Optional[str] = None
    ) -> str:
        """Call Ollama with exponential backoff retry logic"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        for attempt in range(self.max_retries):
            try:
                job_logger.info(f"LLM call attempt {attempt + 1}/{self.max_retries}")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
                    response = await client.post(
                        f"{self.host}/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": "You are an exam evaluator. Return ONLY valid JSON, no thinking tags."},
                                {"role": "user", "content": prompt}
                            ],
                            "stream": False,
                            "options": {
                                "temperature": self.temperature,
                                "top_p": 0.9,
                                "num_predict": 1024,  # Increased for complete responses
                                "num_ctx": 4096
                                # Removed stop tokens - they were causing empty responses
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        resp_json = response.json()
                        content = resp_json.get('message', {}).get('content', '').strip()
                        
                        # Debug: log raw response if empty
                        if not content:
                            job_logger.warning(f"Empty content. Full response: {resp_json}")
                        else:
                            job_logger.info(f"✓ Got response ({len(content)} chars)")
                            return content
                        job_logger.warning("Empty response from model")
                    else:
                        job_logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
                
            except httpx.TimeoutException:
                job_logger.warning(f"Timeout on attempt {attempt + 1}")
            except Exception as e:
                job_logger.error(f"Error: {str(e)}")
            
            # Exponential backoff with jitter
            if attempt < self.max_retries - 1:
                delay = self.base_retry_delay * (2 ** attempt) + random.uniform(0, 1)
                job_logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        raise Exception(f"Failed after {self.max_retries} attempts")
    
    async def evaluate_question(
        self,
        question: QuestionSchema,
        student_answer: str,
        expected_answer: str,
        keywords: Optional[List[str]] = None,
        job_id: Optional[str] = None
    ) -> QuestionEvaluationSchema:
        """Evaluate a single question"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        try:
            job_logger.info(f"Evaluating {question.question_id} ({question.marks}m)")
            
            # Build prompt for this question
            prompt = self._build_question_prompt(question, student_answer, expected_answer, keywords)
            
            # Call model
            response_text = await self._call_ollama_with_retry(prompt, job_id)
            
            # Extract JSON
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                job_logger.error(f"Failed to parse JSON for {question.question_id}")
                # Return zero marks on failure
                return QuestionEvaluationSchema(
                    question_ref=question.question_id,
                    marks_obtained=0.0,
                    max_marks=question.marks,
                    reasoning="Failed to evaluate - JSON parse error",
                    feedback="Please review manually",
                    question_type=question.question_type,
                    evaluated=False
                )
            
            # Validate marks are within bounds
            marks_obtained = float(json_data.get('marks_obtained', 0))
            marks_obtained = max(0, min(marks_obtained, question.marks))
            
            result = QuestionEvaluationSchema(
                question_ref=question.question_id,
                marks_obtained=marks_obtained,
                max_marks=question.marks,
                reasoning=json_data.get('reasoning', 'N/A'),
                feedback=json_data.get('feedback', ''),
                question_type=question.question_type,
                evaluated=True
            )
            
            job_logger.info(f"✓ {question.question_id}: {marks_obtained}/{question.marks}")
            return result
            
        except Exception as e:
            job_logger.error(f"Error evaluating {question.question_id}: {str(e)}")
            return QuestionEvaluationSchema(
                question_ref=question.question_id,
                marks_obtained=0.0,
                max_marks=question.marks,
                reasoning=f"Evaluation failed: {str(e)}",
                feedback="Please review manually",
                question_type=question.question_type,
                evaluated=False
            )
    
    async def evaluate_part(
        self,
        part: PartSchema,
        student_answers: List[Any],
        answer_key: List[Any],
        job_id: Optional[str] = None
    ) -> PartEvaluationSchema:
        """Evaluate all questions in a part with parallel batching for GPU efficiency"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        job_logger.info(f"Evaluating Part {part.part_id} ({len(part.questions)} questions, sequential)")
        
        # Sequential processing to avoid overloading Ollama
        semaphore = asyncio.Semaphore(1)  # 1 = sequential (was 2, causing empty responses)
        
        async def evaluate_with_limit(question, student_ans, expected_ans, keywords):
            async with semaphore:
                return await self.evaluate_question(
                    question=question,
                    student_answer=student_ans,
                    expected_answer=expected_ans,
                    keywords=keywords,
                    job_id=job_id
                )
        
        # Prepare all evaluation tasks
        tasks = []
        for question in part.questions:
            # Find student answer for this question
            student_ans = "Not answered"
            for sa in student_answers:
                if sa.question_ref == question.question_id or sa.question_ref.startswith(question.question_id):
                    student_ans = sa.answer_text
                    break
            
            # Find expected answer
            expected_ans = "Not provided"
            keywords = None
            for ak in answer_key:
                if ak.question_ref == question.question_id or ak.question_ref.startswith(question.question_id):
                    expected_ans = ak.expected_answer
                    keywords = ak.keywords if hasattr(ak, 'keywords') else None
                    break
            
            # Create task with semaphore limit
            tasks.append(evaluate_with_limit(question, student_ans, expected_ans, keywords))
        
        # Execute all tasks concurrently (limited by semaphore)
        question_results = await asyncio.gather(*tasks)
        
        # Calculate total marks
        total_marks = sum(r.marks_obtained for r in question_results)
        
        return PartEvaluationSchema(
            part_id=part.part_id,
            questions_evaluated=list(question_results),
            total_marks_obtained=total_marks,
            max_marks=part.total_marks,
            attempted=part.attempted,
            dropped=False
        )
    
    async def evaluate_section(
        self,
        section_id: str,
        mapping_data: MappingOutputSchema,
        job_id: Optional[str] = None
    ) -> SectionEvaluationSchema:
        """Evaluate a section by evaluating each attempted part"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        section = mapping_data.sections.get(section_id)
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        job_logger.info(f"Evaluating Section {section_id}")
        
        student_answers = mapping_data.student_answers.get(section_id, [])
        answer_key = mapping_data.answer_key.get(section_id, [])
        
        # Evaluate only attempted parts
        part_results = []
        all_question_results = []
        
        for part in section.parts:
            if part.attempted:
                result = await self.evaluate_part(
                    part=part,
                    student_answers=student_answers,
                    answer_key=answer_key,
                    job_id=job_id
                )
                part_results.append(result)
                all_question_results.extend(result.questions_evaluated)
        
        # Apply drop-lowest rule if more than 2 parts were attempted
        dropped_part = None
        if len(part_results) > 2:
            # Find the part with lowest marks
            sorted_parts = sorted(part_results, key=lambda p: p.total_marks_obtained)
            dropped_part = sorted_parts[0].part_id
            sorted_parts[0].dropped = True
            job_logger.info(f"Dropping lowest part: {dropped_part}")
            # Calculate total from top 2 parts only
            total_marks = sum(p.total_marks_obtained for p in sorted_parts[1:])
        else:
            total_marks = sum(p.total_marks_obtained for p in part_results)
        
        # Cap at section max
        total_marks = min(total_marks, section.max_marks)
        
        return SectionEvaluationSchema(
            section_id=section_id,
            parts_evaluated=part_results,
            questions_evaluated=all_question_results,
            total_marks_obtained=total_marks,
            max_marks=section.max_marks,
            questions_answered=len(all_question_results),
            dropped_question=dropped_part,
            remarks=f"Evaluated {len(part_results)} parts"
        )
    
    async def evaluate_exam(
        self,
        mapping_data: MappingOutputSchema,
        job_id: Optional[str] = None
    ) -> EvaluationOutputSchema:
        """Evaluate complete exam - section by section, question by question"""
        job_logger = get_job_logger(job_id, "EVALUATION") if job_id else logger
        
        # Check model availability
        if not await self._check_model_availability():
            raise Exception(f"Model {self.model} not available")
        
        sections_to_evaluate = list(mapping_data.sections.keys())
        job_logger.info(f"Starting evaluation for sections: {sections_to_evaluate}")
        
        # Evaluate sections SEQUENTIALLY (not parallel) to avoid overloading Ollama
        section_results = {}
        for section_id in sections_to_evaluate:
            try:
                result = await self.evaluate_section(section_id, mapping_data, job_id)
                section_results[section_id] = result
                job_logger.info(f"✓ Section {section_id}: {result.total_marks_obtained}/{result.max_marks}")
            except Exception as e:
                job_logger.error(f"Section {section_id} failed: {str(e)}")
                section = mapping_data.sections[section_id]
                section_results[section_id] = SectionEvaluationSchema(
                    section_id=section_id,
                    parts_evaluated=[],
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
            remarks = "Outstanding performance!"
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
                'sections_evaluated': len(section_results),
                'evaluation_type': 'per-question'
            }
        )
        
        job_logger.info(f"✓ Evaluation complete: {total_marks}/{max_possible} ({percentage:.1f}%)")
        return result
    
    def validate_evaluation(self, evaluation: EvaluationOutputSchema) -> EvaluationValidationSchema:
        """Validate evaluation results"""
        warnings = []
        errors = []
        
        if evaluation.total_marks > evaluation.max_total_marks:
            errors.append(f"Total {evaluation.total_marks} > max {evaluation.max_total_marks}")
        
        expected_pct = (evaluation.total_marks / evaluation.max_total_marks * 100) if evaluation.max_total_marks > 0 else 0
        if abs(evaluation.percentage - expected_pct) > 0.1:
            warnings.append(f"Percentage mismatch: {evaluation.percentage} vs {expected_pct:.2f}")
        
        existing_sections = list(evaluation.sections.keys())
        
        return EvaluationValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            marks_within_limits=evaluation.total_marks <= evaluation.max_total_marks,
            section_a_valid='A' in existing_sections,
            section_b_valid='B' in existing_sections,
            section_c_valid='C' in existing_sections
        )
