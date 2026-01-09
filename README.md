# AI Exam Evaluator - Production System

A production-ready AI-powered handwritten exam evaluation system with clean architecture, strict rules enforcement, and safe deployment.

## 🎯 System Overview

This system evaluates handwritten exam answer sheets by:
1. Extracting text from PDFs using OCR.Space API (handwriting capable)
2. Mapping questions, answers, and student responses using **Qwen 2.5 (14B)**
3. Evaluating answers using **DeepSeek-R1 (7B)** with liberal & fair evaluation
4. Outputting strict JSON with marks, feedback, and remarks

## 🏗️ Architecture

```
ai_exam_evaluator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Core services (OCR, Qwen, DeepSeek)
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── rules/          # Evaluation & section rules
│   │   └── config/         # Configuration management
│   ├── requirements.txt
│   └── .env
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API service
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## 🔧 Prerequisites

### Required Software

1. **Python 3.10+**
2. **Node.js 18+** and npm
3. **Ollama** (for running local LLMs)
4. **Poppler** (for PDF to image conversion)

### Required Models

You must install these specific models - DO NOT use `latest`:

```bash
# Install Qwen 2.5 14B for mapping
ollama pull qwen2.5:14b

# Install DeepSeek-R1 7B for evaluation
ollama pull deepseek-r1:7b-qwen-distill-q8_0
```

Verify models are installed:
```bash
ollama list
```

### Installing Poppler (Windows)

1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\poppler`
3. Add `C:\poppler\Library\bin` to PATH

## 🚀 Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

## ⚙️ Configuration

### Environment Variables (.env)

The `.env` file is already configured with your API key:

```env
# OCR.Space API Configuration
OCR_API_KEY=K86163544688957

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Model Configuration (DO NOT CHANGE)
MAPPING_MODEL=qwen2.5:14b
EVALUATION_MODEL=deepseek-r1:7b-qwen-distill-q8_0

# Storage
UPLOAD_DIR=./uploads
RESULTS_DIR=./results

# Server Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
```

### YAML Configuration

All system rules are in `backend/app/config/config.yaml`:
- OCR settings
- Model settings
- Section rules (marks, questions to answer)
- Evaluation rules (strict/liberal modes)

## 🎮 Running the System

### Step 1: Start Ollama

Ensure Ollama is running:

```bash
# Check if Ollama is running
ollama list

# If not running, start Ollama service (usually starts automatically)
```

### Step 2: Start Backend

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Run FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Step 3: Start Frontend

```bash
cd frontend

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 📋 Question Paper Format

### Structure Requirements

- **Exactly 3 sections**: A, B, C
- **Exactly 3 questions per section**: A1, A2, A3 | B1, B2, B3 | C1, C2, C3

### Subdivision Rules

- Normal subdivisions: (i), (ii), (iii), (iv)
- ONE section may have only 2 subdivisions
- Nested subdivisions: numeric (1, 2, 3) OR alphabetic (a, b, c)

### Marks Specification

- Marks must be explicitly stated: `[5 marks]`, `(5 marks)`, `[5m]`
- If not stated, system will not assume marks

### Example Question Structure

```
SECTION A

A1. What is machine learning? [2 marks]

A2. Explain the following: [8 marks]
    (i) Supervised learning
    (ii) Unsupervised learning

A3. Answer the following: [10 marks]
    (i) Define neural networks
        a. What is a perceptron?
        b. Explain activation functions
    (ii) Describe deep learning
```

## 📝 Answering Rules

### Section Rules

- Student must answer **2 out of 3** questions in each section
- If student answers all 3:
  - All 3 are evaluated
  - **Lowest scoring question is automatically dropped**
  - Only top 2 count toward final marks

### Mark Caps

- Section A: Maximum 10 marks
- Section B: Maximum 20 marks
- Section C: Maximum 20 marks
- **Total: 50 marks**

## ⚖️ Evaluation Rules

### 1-Mark Questions (STRICT)
- ✅ Correct → Full mark
- ❌ Incorrect → Zero
- ❌ No partial marks
- ❌ No liberal interpretation

### True/False Questions (STRICT)
- Only T/F answer matters
- No marks for explanations
- Correct → Full mark
- Incorrect → Zero

### Multi-Mark Questions (LIBERAL)
- ✅ Concept-based evaluation
- ✅ Different wording accepted
- ✅ Partial marks for partial understanding
- ✅ Focus on core ideas
- ❌ Only penalize completely wrong concepts

### Language Rules (NEVER PENALIZE)
- ❌ Never penalize spelling mistakes
- ❌ Never penalize grammar errors
- ❌ Never penalize handwriting OCR noise
- ✅ Focus ONLY on conceptual correctness

## 🔄 System Workflow

### 1. File Upload
Frontend uploads 3 PDFs → Backend creates job → Returns job_id

### 2. OCR Extraction
- Converts PDFs to images (200 DPI)
- Compresses images to <900KB
- Parallel OCR processing (3 workers)
- Extracts text using OCR.Space API

### 3. Preprocessing
- Cleans OCR text
- Extracts sections (A, B, C)
- Normalizes question labels
- Extracts student ID

### 4. Mapping (Qwen 2.5)
- Parses question structure
- Maps answer key entries
- Matches student answers to questions
- Outputs strict JSON (no evaluation)

### 5. Evaluation (DeepSeek-R1)
- Applies evaluation rules (strict/liberal)
- Assigns marks per question
- Drops lowest if student answered all 3
- Generates feedback and remarks

### 6. Result Delivery
- Validates final output
- Returns JSON with marks and feedback
- Available for download

## 🌐 API Endpoints

### Upload Files
```http
POST /api/upload
Content-Type: multipart/form-data

Form Data:
- question_paper: PDF file
- answer_key: PDF file
- student_answers: PDF file

Response:
{
  "job_id": "uuid",
  "message": "Files uploaded successfully",
  "status": "pending"
}
```

### Get Status
```http
GET /api/status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "processing|completed|failed",
  "current_step": "mapping",
  "progress_percentage": 75.0
}
```

### Get Result
```http
GET /api/result/{job_id}?include_mapping=false

Response:
{
  "job_id": "uuid",
  "status": "completed",
  "evaluation": {
    "student_id": "...",
    "sections": { ... },
    "total_marks": 45,
    "percentage": 90.0,
    "remarks": "Excellent performance"
  }
}
```

### Download Result
```http
GET /api/result/{job_id}/download

Response: JSON file download
```

## 📊 Output Format

### Final JSON Structure

```json
{
  "student_id": "12345",
  "sections": {
    "A": {
      "section_id": "A",
      "questions_evaluated": [
        {
          "question_ref": "A1",
          "marks_obtained": 8.5,
          "max_marks": 10,
          "reasoning": "Strong conceptual understanding...",
          "feedback": "Excellent answer with clear examples",
          "evaluated": true,
          "dropped": false
        }
      ],
      "total_marks_obtained": 8.5,
      "max_marks": 10,
      "dropped_question": "A3"
    },
    "B": { ... },
    "C": { ... }
  },
  "total_marks": 45.0,
  "max_total_marks": 50.0,
  "percentage": 90.0,
  "remarks": "Outstanding performance!"
}
```

## 🐛 Troubleshooting

### Ollama Connection Error
```
Error: Connection refused to localhost:11434
```
**Solution**: Ensure Ollama is running. Check with `ollama list`

### Model Not Found
```
Error: Model qwen2.5:14b not found
```
**Solution**: Pull the required models:
```bash
ollama pull qwen2.5:14b
ollama pull deepseek-r1:7b-qwen-distill-q8_0
```

### OCR API Error
```
Error: OCR_API_KEY not found
```
**Solution**: Verify `.env` file exists with correct API key

### Poppler Not Found (Windows)
```
Error: Unable to get page count. Is poppler installed?
```
**Solution**: Install Poppler and add to PATH

### Port Already in Use
```
Error: Port 8000 already in use
```
**Solution**: Kill existing process or change port in config

## 🔒 Security Notes

### Production Deployment

1. **Environment Variables**
   - Never commit `.env` to version control
   - Use secure key management in production
   - Rotate API keys regularly

2. **CORS Configuration**
   - Update `allow_origins` in `main.py` for production
   - Set to specific frontend domain

3. **File Upload**
   - Validate file types and sizes
   - Scan for malware
   - Set upload limits

4. **API Rate Limiting**
   - Implement rate limiting on endpoints
   - Monitor OCR API usage

## 📦 Docker Deployment (Optional)

### Backend Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install poppler
RUN apt-get update && apt-get install -y poppler-utils

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/results:/app/results

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

## 🧪 Testing

### Test with Sample Files

1. Create sample question paper with sections A, B, C
2. Create answer key with expected answers
3. Create student answer sheet (can be handwritten photo converted to PDF)
4. Upload through UI
5. Monitor progress
6. Verify results

### Validation Checks

- ✅ Section structure parsed correctly
- ✅ Questions mapped to student answers
- ✅ Marks within limits
- ✅ Lowest score dropped when needed
- ✅ Evaluation rules applied correctly

## 📞 Support

For issues or questions:
1. Check logs: `backend/logs/app.log`
2. Verify configuration: `backend/app/config/config.yaml`
3. Test endpoints: `http://localhost:8000/docs`

## 📄 License

Production System v1.0.0 - © 2026

## 🎓 Key Features

✅ **Production-Ready**: Clean architecture, error handling, logging  
✅ **Handwriting Support**: OCR.Space API with Engine 2  
✅ **Fixed Models**: Qwen 2.5 (14B) + DeepSeek-R1 (7B)  
✅ **Strict Rules**: Section constraints, mark caps, auto-drop lowest  
✅ **Fair Evaluation**: Liberal for concepts, strict for 1-mark questions  
✅ **Background Processing**: Async job queue with progress tracking  
✅ **YAML Configuration**: No hardcoded values  
✅ **Schema Validation**: Pydantic models for data integrity  
✅ **Complete API**: Upload, status polling, result download  
✅ **Modern UI**: React frontend with drag-drop upload  

---

**System Status**: Production Ready ✅  
**Version**: 1.0.0  
**Last Updated**: January 2026
