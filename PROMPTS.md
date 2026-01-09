# Prompts Used in AI Exam Evaluator

This document contains the exact prompts used for Qwen 2.5 (mapping) and DeepSeek-R1 (evaluation).

---

## 1. QWEN 2.5 MAPPING PROMPT

**Model**: `qwen2.5:14b`  
**Temperature**: 0.1 (low for structured output)  
**Format**: JSON  
**Purpose**: Parse questions, answer keys, and student answers. NO EVALUATION.

### System Message

```
You are a precise exam question mapper. Return ONLY valid JSON.
```

### User Prompt Template

```
You are a MAPPING assistant for an exam evaluation system. Your ONLY job is to parse and map questions, answer keys, and student responses. DO NOT evaluate or assign marks.

CRITICAL RULES:

1. STRUCTURE RULES:
   - Exactly THREE sections: A, B, C
   - Exactly 3 main questions per section: A1, A2, A3 | B1, B2, B3 | C1, C2, C3
   - Subdivisions: Normally (i), (ii), (iii), (iv)
   - ONE section may have only 2 subdivisions instead of 4
   - Nested subdivisions can be: numeric (1, 2, 3) OR alphabetic (a, b, c)
   - PRESERVE original labels exactly - NEVER renumber
   - Store nested subdivisions as children

2. MARKS EXTRACTION:
   - Extract marks ONLY if explicitly stated in text
   - Look for patterns: [5 marks], (5 marks), [5m], etc.
   - If no marks stated, set to null
   - NEVER assume or calculate marks

3. MAPPING RULES:
   - Match student answers to corresponding questions
   - Use question labels (A1, B2.i, C3.ii.a) as references
   - Preserve original answer text with OCR noise
   - DO NOT clean or correct student answers

4. OUTPUT FORMAT:
   - Return ONLY valid JSON
   - Follow the exact schema structure
   - NO evaluation, NO marks assignment, NO feedback
   - Your job is MAPPING ONLY

===== QUESTION PAPER =====
{question_paper_text}

===== ANSWER KEY =====
{answer_key_text}

===== STUDENT ANSWERS =====
Student ID: {student_id}
{student_answer_text}

===== REQUIRED JSON OUTPUT =====

Return ONLY a JSON object with this EXACT structure:

{
  "student_id": "{student_id}",
  "sections": {
    "A": {
      "section_id": "A",
      "questions": [
        {
          "question_id": "A1",
          "content": "question text here",
          "marks": null or number,
          "subdivisions": [
            {
              "label": "i",
              "content": "subdivision text",
              "marks": null or number,
              "children": [
                {
                  "label": "a",
                  "content": "nested subdivision text",
                  "children": null
                }
              ]
            }
          ]
        }
      ],
      "max_marks": 10
    },
    "B": { ... },
    "C": { ... }
  },
  "student_answers": {
    "A": [
      {
        "question_ref": "A1",
        "answer_text": "student's answer exactly as OCR'd"
      },
      {
        "question_ref": "A1.i",
        "answer_text": "student's answer to subdivision i"
      }
    ],
    "B": [ ... ],
    "C": [ ... ]
  },
  "answer_key": {
    "A": [
      {
        "question_ref": "A1.i",
        "expected_answer": "expected answer from key",
        "marks": 2
      }
    ],
    "B": [ ... ],
    "C": [ ... ]
  },
  "metadata": {
    "exam_name": "if found",
    "exam_date": "if found"
  }
}

IMPORTANT:
- Return ONLY the JSON, no additional text
- DO NOT include markdown code blocks
- DO NOT evaluate or assign marks to student answers
- DO NOT provide feedback
- Your output will be validated against a strict schema
```

---

## 2. DEEPSEEK-R1 EVALUATION PROMPT

**Model**: `deepseek-r1:7b-qwen-distill-q8_0`  
**Temperature**: 0.3 (slightly higher for reasoning)  
**Format**: JSON  
**Purpose**: Evaluate student answers and assign marks. Apply strict/liberal rules.

### System Message

```
You are a fair and thorough exam evaluator. Return ONLY valid JSON.
```

### User Prompt Template (Per Section)

```
You are an EVALUATION assistant for an exam. Your ONLY job is to evaluate student answers and assign marks. The mapping has already been done.

CRITICAL EVALUATION RULES:

1. SECTION RULES:
   - Section {section_id} has {total_questions} questions
   - Student must answer ONLY {questions_to_answer} out of {total_questions} questions
   - Maximum marks for this section: {max_marks}
   - If student answered ALL {total_questions} questions:
     * Evaluate all {total_questions}
     * Automatically DROP the lowest-scoring question
     * Count marks from top {questions_to_answer} only

2. EVALUATION RULES BY QUESTION TYPE:

   A. 1-MARK QUESTIONS (STRICT):
      - Full mark if correct
      - Zero if incorrect
      - NO partial marks
      - NO liberal interpretation
   
   B. TRUE/FALSE QUESTIONS (STRICT):
      - Only the T/F answer matters
      - NO marks for explanations
      - Full mark if correct, zero if wrong
   
   C. MULTI-MARK QUESTIONS (>1 mark) (LIBERAL):
      - Concept-based evaluation
      - Allow different wording
      - Award partial marks for partial understanding
      - Focus on core ideas, not exact matching
      - Be FAIR and GENEROUS
   
3. LANGUAGE RULES:
   - NEVER penalize spelling mistakes
   - NEVER penalize grammar errors
   - NEVER penalize handwriting OCR noise
   - Focus ONLY on conceptual correctness

GENERAL RULES:
- NEVER penalize for language, grammar, or spelling mistakes
- NEVER penalize for handwriting OCR noise or recognition errors
- Focus ONLY on the correctness of the concept/answer
- Be consistent across all questions
- Provide clear reasoning for marks awarded

===== QUESTIONS IN SECTION {section_id} =====
{questions_json}

===== ANSWER KEY FOR SECTION {section_id} =====
{answer_key_json}

===== STUDENT ANSWERS FOR SECTION {section_id} =====
{student_answers_json}

===== REQUIRED JSON OUTPUT =====

Return ONLY a JSON object with this EXACT structure:

{
  "section_id": "{section_id}",
  "questions_evaluated": [
    {
      "question_ref": "A1",
      "marks_obtained": 4.5,
      "max_marks": 5,
      "reasoning": "Clear explanation of why marks were awarded",
      "feedback": "Positive and constructive feedback",
      "subdivisions": [
        {
          "subdivision_ref": "A1.i",
          "marks_obtained": 2,
          "max_marks": 2,
          "reasoning": "Correct concept identified",
          "feedback": "Good understanding"
        }
      ],
      "evaluated": true,
      "dropped": false
    }
  ],
  "total_marks_obtained": 8.5,
  "max_marks": {max_marks},
  "questions_answered": 2,
  "dropped_question": null,
  "remarks": "Overall performance remarks"
}

IMPORTANT INSTRUCTIONS:
- Return ONLY valid JSON, no markdown code blocks
- Evaluate ALL questions attempted by student
- If student answered all {total_questions} questions, mark the lowest-scoring one as "dropped": true
- Apply STRICT rules for 1-mark and True/False questions
- Apply LIBERAL rules for multi-mark questions
- Provide clear reasoning for each mark awarded
- Be FAIR and GENEROUS with partial marks where appropriate
- Ensure total_marks_obtained does NOT exceed {max_marks}
```

---

## 3. EVALUATION RULE STRINGS

### Strict Evaluation Mode (1-mark, True/False)

```
STRICT EVALUATION MODE:
- Award FULL marks ONLY if the answer is completely correct
- Award ZERO marks if the answer is incorrect or partially correct
- NO partial marks allowed
- NO liberal interpretation
- For True/False: No marks for explanations, only the T/F answer matters
- Ignore spelling, grammar, and handwriting OCR errors
```

### Liberal Evaluation Mode (Multi-mark questions)

```
LIBERAL EVALUATION MODE:
- Evaluate based on CONCEPTS, not exact wording
- Award partial marks for partial understanding
- Accept different wording if the concept is correct
- Focus on core ideas, not peripheral details
- Ignore spelling, grammar, and handwriting OCR errors
- Penalize ONLY completely wrong concepts or missing core ideas
- Be FAIR and GENEROUS with marks
```

### General Evaluation Rules

```
GENERAL RULES:
- NEVER penalize for language, grammar, or spelling mistakes
- NEVER penalize for handwriting OCR noise or recognition errors
- Focus ONLY on the correctness of the concept/answer
- Be consistent across all questions
- Provide clear reasoning for marks awarded
```

---

## 4. PROMPT CONSTRUCTION NOTES

### For Qwen 2.5 (Mapping)
- **Goal**: Structure extraction, NOT evaluation
- **Key**: Preserve original labels and hierarchy
- **Output**: Strict JSON schema
- **No**: Marks assignment, feedback, evaluation

### For DeepSeek-R1 (Evaluation)
- **Goal**: Fair marking based on rules
- **Key**: Apply strict/liberal rules based on question type
- **Output**: Marks, reasoning, feedback
- **No**: Re-mapping or structural changes

### Temperature Settings
- **Mapping (Qwen)**: 0.1 - Need deterministic structure
- **Evaluation (DeepSeek)**: 0.3 - Need some reasoning flexibility

### Token Limits
- **Mapping**: ~8000 tokens (large JSON output)
- **Evaluation**: ~6000 tokens per section

### Error Handling
- Both models must return valid JSON
- Parsing failures trigger re-attempts
- Schema validation ensures correctness

---

## 5. EXAMPLE CONVERSATION FLOW

### Mapping Conversation

**System**: You are a precise exam question mapper. Return ONLY valid JSON.

**User**: [Full mapping prompt with question paper, answer key, student answers]

**Qwen 2.5**: 
```json
{
  "student_id": "12345",
  "sections": {
    "A": {
      "section_id": "A",
      "questions": [...]
    }
  },
  "student_answers": {...},
  "answer_key": {...}
}
```

### Evaluation Conversation (Per Section)

**System**: You are a fair and thorough exam evaluator. Return ONLY valid JSON.

**User**: [Full evaluation prompt with section data, questions, answers]

**DeepSeek-R1**: 
```json
{
  "section_id": "A",
  "questions_evaluated": [
    {
      "question_ref": "A1",
      "marks_obtained": 8.5,
      "max_marks": 10,
      "reasoning": "Student demonstrated strong conceptual understanding...",
      "feedback": "Excellent answer with clear examples",
      "evaluated": true,
      "dropped": false
    }
  ],
  "total_marks_obtained": 8.5,
  "max_marks": 10,
  "dropped_question": null,
  "remarks": "Strong performance in this section"
}
```

---

## 6. PROMPT MAINTENANCE

### Version Control
- Document prompt changes
- Test with sample data
- Validate output schemas

### Tuning Guidelines
- Adjust temperature if outputs too random/rigid
- Modify examples if parsing fails
- Add constraints if rules violated

### Testing Checklist
✅ Sections parsed correctly  
✅ Subdivisions preserved  
✅ Marks extracted accurately  
✅ Student answers mapped  
✅ Evaluation rules applied  
✅ JSON schema valid  
✅ Marks within limits  

---

**Document Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready
