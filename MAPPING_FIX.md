# 🔧 Qwen Mapping JSON Error - Fixed

## Problem
Qwen 2.5 was returning malformed JSON with unterminated strings:
```
❌ Invalid JSON from mapping model: Unterminated string starting at: line 1094 column 26 (char 36604)
```

## Root Causes
1. **Token limit too low** - 8000 tokens insufficient for complex responses
2. **No truncation handling** - Model responses getting cut off mid-JSON
3. **No markdown extraction** - If model wrapped JSON in code blocks
4. **No repair logic** - Couldn't recover from malformed JSON

## Fixes Applied

### 1. Enhanced JSON Parsing ([qwen_mapper.py](backend/app/services/qwen_mapper.py))

**Added comprehensive error recovery:**
- ✅ Increased `num_predict` from 8000 → **12000 tokens**
- ✅ Added markdown code block extraction
- ✅ Added JSON repair for truncated responses
- ✅ Better logging (shows first/last 200 chars of response)
- ✅ Multiple fallback strategies

**New error handling chain:**
```python
1. Try direct json.loads()
2. If fails → Extract from markdown (```json ... ```)
3. If fails → Repair truncated JSON (close unterminated strings/objects)
4. If fails → Extract JSON object from anywhere in response
5. If all fail → Detailed error with context
```

### 2. JSON Repair Function

**Added `_repair_truncated_json()` method:**
- Closes unterminated strings (`"`)
- Closes unclosed arrays (`]`)
- Closes unclosed objects (`}`)
- Handles escaped characters properly

### 3. Improved Prompt Instructions

**Enhanced prompt to emphasize:**
```
CRITICAL INSTRUCTIONS:
- Return ONLY the JSON object, no additional text
- DO NOT wrap in markdown code blocks
- Ensure ALL strings are properly terminated with closing quotes
- Ensure ALL objects and arrays are properly closed
- Make sure the JSON is complete and not truncated
- Your entire response must be parseable by json.loads()
```

### 4. Better Model Configuration

**Optimized Ollama parameters:**
```python
options={
    'temperature': 0.1,        # Low temp for consistency
    'num_predict': 12000,      # Large enough for complete response
    'top_p': 0.95,             # Nucleus sampling
    'top_k': 40,               # Top-k sampling
    'repeat_penalty': 1.1      # Prevent repetition
},
stream=False  # Ensure complete response
```

## Testing

### Quick Test
Run the test script to verify mapping works:
```bash
cd backend
python test_mapping.py
```

This will:
- ✅ Test mapping with sample data
- ✅ Validate JSON structure
- ✅ Show any errors with full traceback
- ✅ Display mapping results

### Full Integration Test
1. Start backend: `uvicorn app.main:app --reload --port 8000`
2. Upload 3 PDFs via frontend
3. Check terminal logs for:
   ```
   Job xxx | MAPPING | Started - Qwen 2.5 14B model
   Job xxx | MAPPING | Building structured mapping prompt...
   Job xxx | MAPPING | Sending request to Qwen (this may take 20-40s)...
   Job xxx | MAPPING | ✓ Completed - 3 sections mapped
   ```

## What to Expect

### Normal Output
```
2026-01-07 12:00:00 | INFO | Job xxx | MAPPING | Started - Qwen 2.5 14B model
2026-01-07 12:00:00 | INFO | Job xxx | MAPPING | Building structured mapping prompt...
2026-01-07 12:00:00 | INFO | Job xxx | MAPPING | Sending request to Qwen...
2026-01-07 12:00:30 | INFO | Job xxx | MAPPING | ✓ Completed - 3 sections mapped
```

### If JSON Needs Repair (Warning but still works)
```
2026-01-07 12:00:30 | WARNING | JSON appears truncated, attempting to repair...
2026-01-07 12:00:30 | INFO | Successfully repaired truncated JSON
2026-01-07 12:00:30 | INFO | Job xxx | MAPPING | ✓ Completed - 3 sections mapped
```

### If Still Fails (Detailed Error)
```
2026-01-07 12:00:30 | ERROR | Failed to parse JSON response: ...
2026-01-07 12:00:30 | ERROR | Response length: 45000 chars
2026-01-07 12:00:30 | ERROR | Context around error (chars 36500:36700): ...
2026-01-07 12:00:30 | ERROR | Job xxx | MAPPING | ✗ Failed - Invalid JSON...
```

## Additional Improvements

### 1. Increased Robustness
- Handles model quirks (markdown wrapping, thinking tokens, etc.)
- Graceful degradation with multiple fallback strategies
- Detailed error context for debugging

### 2. Better Logging
- Shows response length and preview
- Logs repair attempts
- Displays exact error position in JSON

### 3. Model Instructions
- Clearer prompt about JSON format
- Explicit instructions to avoid truncation
- Emphasis on complete, parseable output

## Similar Fixes Applied

The same improvements were also applied to **DeepSeek evaluator** ([deepseek_evaluator.py](backend/app/services/deepseek_evaluator.py)):
- Thinking token removal (`<think>...</think>`)
- Markdown extraction
- JSON repair logic
- Increased token limits (8000)

## Next Steps

1. **Restart backend server** to load the fixes
2. **Test with your PDFs** - the mapping should now work
3. **Monitor logs** - check for any warnings about JSON repair
4. **If issues persist**:
   - Run `python test_mapping.py` for debugging
   - Check if model has enough VRAM (14B model needs ~8-10GB)
   - Verify Ollama is running: `curl http://localhost:11434/api/tags`

## Prevention

To avoid future issues:
- Keep model responses under 12000 tokens
- Use simpler prompt if dealing with very long documents
- Consider splitting large exams into multiple sections
- Monitor VRAM usage during inference

---

**Status**: ✅ Fixed - Ready for testing
**Files Modified**: 2 (qwen_mapper.py, deepseek_evaluator.py)
**Test Script Added**: test_mapping.py
