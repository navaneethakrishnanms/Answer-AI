"""Qwen 2.5 Mapping Service - MAPPING ONLY, NO EVALUATION (Async Optimized)"""

import httpx
import json
import logging
import re
import asyncio
from typing import Dict, Any, Optional
from app.config import Config
from app.schemas.mapping_schema import MappingOutputSchema, MappingValidationSchema
from app.rules import SectionRules
from app.logger import log_stage_start, log_stage_complete, log_progress, log_stage_error, get_job_logger

logger = logging.getLogger(__name__)


class QwenMapperService:
    """Service for mapping questions, answers, and student responses using Qwen 2.5 (Async)"""
    
    def __init__(self):
        self.host = Config.get_ollama_host()
        self.model = Config.get_model('mapping')
        self.temperature = Config.get('ollama.temperature.mapping', 0.05)
        self.max_retries = 3
        self.base_retry_delay = 2
        
        logger.info(f"Qwen Mapper initialized: {self.model} (async httpx)")
    
    async def _check_model_availability(self) -> bool:
        """Check if model is available (async)"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.host}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    available = any(m['name'] == self.model for m in models)
                    if not available:
                        logger.warning(f"Model {self.model} not found. Please run: ollama pull {self.model}")
                    else:
                        logger.info(f"Model {self.model} is available")
                    return available
        except Exception as e:
            logger.error(f"Model check failed: {str(e)}")
        return False
    
    def _repair_truncated_json(self, json_str: str) -> str:
        """
        Attempt to repair truncated JSON by closing open structures
        """
        # Count open and close braces/brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Check if string is unterminated
        in_string = False
        escaped = False
        for char in json_str:
            if escaped:
                escaped = False
                continue
            if char == '\\':
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
        
        # If we're in an unterminated string, close it
        if in_string:
            json_str += '"'
        
        # Close any open arrays
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        
        # Close any open objects
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        
        return json_str
    
    def _build_mapping_prompt(self, preprocessed_data: Dict[str, Any]) -> str:
        """
        Build a simplified mapping prompt for Qwen.
        Uses Section → Part → Question hierarchy.
        """
        qp_text = preprocessed_data['question_paper']['full_text']
        ak_text = preprocessed_data['answer_key']['full_text']
        sa_text = preprocessed_data['student_answers']['full_text']
        student_id = preprocessed_data['student_answers'].get('student_id', '')
        
        prompt = f"""You are a MAPPING assistant. Parse the exam and return JSON.

## EXAM STRUCTURE
- 3 Sections: A, B, C
- Each Section has 3 Parts (e.g., A1, A2, A3)
- Each Part has multiple Questions with marks (1m, 2m, 4m, etc.)
- Student answers exactly 2 out of 3 Parts per Section

## CRITICAL: OCR ERROR HANDLING
The text has OCR errors. You MUST:
1. Correct obvious spelling/OCR errors (e.g., "Part A1" might appear as "PartA1", "Part A 1", etc.)
2. Match content SEMANTICALLY, not just by exact text
3. Use question context to determine which part a question belongs to
4. If student writes "Part A1" or just answers questions from Part A1, mark A1 as attempted

## YOUR TASK
1. Parse all sections, parts, and questions from the Question Paper (source of truth for structure)
2. Extract marks for each question (look for [2m], (4 marks), 1M, 2M, etc.)
3. Match student answers to questions by CONTENT/MEANING, not just by number
4. ONLY mark parts as attempted=true if the student ACTUALLY WROTE ANSWERS for that part

## CRITICAL MAPPING RULES
- Use Question Paper to determine the correct structure (Section → Part → Question)
- Use Answer Key to find expected answers for each question
- Look at Student Answers carefully to see which PARTS they actually attempted
- If student only wrote answers for A1 and A2, do NOT mark A3 as attempted
- Match student responses to questions by meaning/topic, not just order

## INPUTS

### QUESTION PAPER (Source of Truth for Structure)
{qp_text}

### ANSWER KEY (Source of Truth for Expected Answers)
{ak_text}

### STUDENT ANSWERS (What the student actually wrote - ID: {student_id})
{sa_text}

## OUTPUT FORMAT (JSON ONLY)

Return ONLY this JSON structure, nothing else:

{{
  "student_id": "{student_id}",
  "sections": {{
    "A": {{
      "section_id": "A",
      "parts": [
        {{
          "part_id": "A1",
          "title": "Part title if any",
          "questions": [
            {{
              "question_id": "A1.1",
              "content": "Question text",
              "marks": 2.0,
              "question_type": "multi-mark",
              "subdivisions": null
            }}
          ],
          "total_marks": 5.0,
          "attempted": true
        }},
        {{
          "part_id": "A2",
          "title": null,
          "questions": [...],
          "total_marks": 5.0,
          "attempted": true
        }},
        {{
          "part_id": "A3",
          "title": null,
          "questions": [...],
          "total_marks": 5.0,
          "attempted": false
        }}
      ],
      "max_marks": 10.0,
      "parts_to_answer": 2
    }},
    "B": {{ ... similar structure ... }},
    "C": {{ ... similar structure ... }}
  }},
  "student_answers": {{
    "A": [
      {{"question_ref": "A1.1", "answer_text": "Student's answer...", "part_id": "A1"}}
    ],
    "B": [...],
    "C": [...]
  }},
  "answer_key": {{
    "A": [
      {{"question_ref": "A1.1", "expected_answer": "Expected answer", "marks": 2.0, "keywords": ["key1", "key2"]}}
    ],
    "B": [...],
    "C": [...]
  }},
  "attempted_parts": {{
    "A": ["A1", "A2"],
    "B": ["B1", "B2"],
    "C": ["C2", "C3"]
  }},
  "metadata": {{
    "exam_name": "if found",
    "total_questions": 0
  }}
}}

## RULES
1. question_type: "1-mark" for 1m, "true-false" for T/F, "multi-mark" otherwise
2. Set attempted=true ONLY for parts the student actually wrote answers for
3. All marks must be numbers (float), not strings
4. Return ONLY the JSON, no markdown, no explanation
5. Start with {{ and end with }}
6. If student didn't attempt a part, still include it in sections but set attempted=false
"""
        return prompt
    
    async def _call_ollama_with_retry(
        self, 
        prompt: str, 
        job_id: Optional[str] = None
    ) -> str:
        """Call Ollama with exponential backoff retry logic (async, non-blocking)"""
        job_logger = get_job_logger(job_id, "MAPPING") if job_id else logger
        
        import random
        
        for attempt in range(self.max_retries):
            try:
                job_logger.info(f"LLM call attempt {attempt + 1}/{self.max_retries}")
                
                # Use async httpx for non-blocking GPU inference
                async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
                    response = await client.post(
                        f"{self.host}/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": "You are a precise exam question mapper. Return ONLY valid JSON. No explanations."},
                                {"role": "user", "content": prompt}
                            ],
                            "stream": False,
                            "format": "json",
                            "options": {
                                "temperature": self.temperature,
                                "num_predict": 32000,
                                "top_p": 0.9,
                                "top_k": 40,
                                "repeat_penalty": 1.05,
                                "num_ctx": 8192  # Reduced from 16384 for better VRAM efficiency
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        content = response.json().get('message', {}).get('content', '').strip()
                        if content:
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
        
        raise Exception(f"Mapping failed after {self.max_retries} attempts")
    
    async def map_exam_data(self, preprocessed_data: Dict[str, Any], job_id: Optional[str] = None) -> MappingOutputSchema:
        """
        Map exam data using Qwen 2.5 (async, non-blocking)
        
        Args:
            preprocessed_data: Preprocessed data from preprocessing service
            job_id: Optional job ID for logging
        
        Returns:
            MappingOutputSchema object
        
        Raises:
            Exception if mapping fails
        """
        job_logger = get_job_logger(job_id, "MAPPING") if job_id else logger
        job_logger.info("Starting exam data mapping with Qwen 2.5 (async)")
        
        try:
            # Check model availability first
            if not await self._check_model_availability():
                raise Exception(f"Model {self.model} not available")
            
            prompt = self._build_mapping_prompt(preprocessed_data)
            job_logger.debug(f"Sending prompt to {self.model} (length: {len(prompt)} chars)")
            
            # Use async call with retry
            response_text = await self._call_ollama_with_retry(prompt, job_id)
            
            # Check if response is empty
            if not response_text:
                job_logger.error("Empty response from mapping model")
                raise ValueError("Empty response from mapping model")
            
            job_logger.debug(f"Received response (length: {len(response_text)} chars)")
            job_logger.debug(f"Response preview (first 200 chars): {response_text[:200]}")
            
            # Parse JSON with robust error handling
            try:
                mapping_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                job_logger.error(f"Failed to parse JSON response: {str(e)}")
                job_logger.error(f"Error at position {e.pos}")
                
                # Try to extract JSON from markdown if present
                if '```json' in response_text or '```' in response_text:
                    try:
                        job_logger.info("Attempting to extract JSON from markdown code block...")
                        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1).strip()
                            mapping_data = json.loads(json_str)
                            job_logger.info("Successfully extracted JSON from markdown")
                        else:
                            raise ValueError("Could not find JSON in markdown")
                    except Exception as extract_error:
                        job_logger.error(f"Failed to extract from markdown: {extract_error}")
                        raise ValueError(f"Invalid JSON from mapping model: {str(e)}")
                
                # Try to fix truncated JSON
                elif response_text.startswith('{'):
                    try:
                        job_logger.warning("JSON appears truncated, attempting to repair...")
                        repaired_json = self._repair_truncated_json(response_text)
                        mapping_data = json.loads(repaired_json)
                        job_logger.info("Successfully repaired truncated JSON")
                    except Exception as repair_error:
                        job_logger.error(f"Failed to repair JSON: {repair_error}")
                        raise ValueError(f"Invalid JSON from mapping model: {str(e)}")
                else:
                    # Try to find JSON object anywhere in response
                    try:
                        job_logger.info("Attempting to extract JSON object from response...")
                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            mapping_data = json.loads(json_str)
                            job_logger.info("Successfully extracted JSON object")
                        else:
                            raise ValueError("No JSON object found in response")
                    except Exception as extract_error:
                        job_logger.error(f"Failed to extract JSON: {extract_error}")
                        raise ValueError(f"Invalid JSON from mapping model: {str(e)}")
            # Log warning if important fields are missing from LLM response
            missing_fields = []
            if 'student_answers' not in mapping_data or not mapping_data.get('student_answers'):
                missing_fields.append('student_answers')
            if 'answer_key' not in mapping_data or not mapping_data.get('answer_key'):
                missing_fields.append('answer_key')
            if 'sections' not in mapping_data or not mapping_data.get('sections'):
                missing_fields.append('sections')
            
            if missing_fields:
                job_logger.warning(f"LLM response missing fields: {missing_fields}. Schema will use defaults.")
            
            # Validate against schema (schema will normalize and add defaults)
            mapping_output = MappingOutputSchema(**mapping_data)
            
            job_logger.info("Mapping completed successfully")
            
            return mapping_output
        
        except Exception as e:
            job_logger.error(f"Error during mapping: {str(e)}")
            raise
    
    def validate_mapping(self, mapping_output: MappingOutputSchema) -> MappingValidationSchema:
        """
        Validate mapping output against rules
        """
        errors = []
        warnings = []
        
        # Check sections exist
        required_sections = {'A', 'B', 'C'}
        found_sections = set(mapping_output.sections.keys())
        
        if found_sections != required_sections:
            missing = required_sections - found_sections
            if missing:
                errors.append(f"Missing sections: {missing}")
        
        # Validate each section has parts
        for section_id, section_data in mapping_output.sections.items():
            if not section_data.parts:
                errors.append(f"Section {section_id} has no parts")
            elif len(section_data.parts) < 3:
                warnings.append(f"Section {section_id} has only {len(section_data.parts)} parts (expected 3)")
            
            # Check that at least 2 parts are attempted
            attempted_count = sum(1 for p in section_data.parts if p.attempted)
            if attempted_count < 2:
                warnings.append(f"Section {section_id}: only {attempted_count} parts marked as attempted")
        
        # Check student answers exist
        if not mapping_output.student_answers:
            warnings.append("No student answers found")
        
        # Check answer key exists
        if not mapping_output.answer_key:
            warnings.append("No answer key found")
        
        return MappingValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
