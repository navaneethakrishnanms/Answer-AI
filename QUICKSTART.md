# 🚀 Quick Start Guide - AI Exam Evaluator

Get the system running in 5 minutes!

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ and npm installed
- [ ] Ollama installed and running
- [ ] Poppler installed (for PDF processing)

## Step 1: Install Required Models (5 minutes)

```powershell
# Open PowerShell and run:

# Install Qwen 2.5 14B (mapping model) - ~8GB download
ollama pull qwen2.5:14b

# Install DeepSeek-R1 7B (evaluation model) - ~4GB download
ollama pull deepseek-r1:7b-qwen-distill-q8_0

# Verify models are installed
ollama list
```

**Expected output:**
```
NAME                                  ID              SIZE
qwen2.5:14b                          ...             8.0 GB
deepseek-r1:7b-qwen-distill-q8_0    ...             4.3 GB
```

## Step 2: Setup Backend (2 minutes)

```powershell
# Navigate to backend directory
cd C:\Projects\Paper_AI\backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Setup Frontend (2 minutes)

```powershell
# Open a NEW PowerShell window
cd C:\Projects\Paper_AI\frontend

# Install dependencies
npm install
```

## Step 4: Start Services (1 minute)

### Terminal 1 - Backend

```powershell
cd C:\Projects\Paper_AI\backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend

```powershell
cd C:\Projects\Paper_AI\frontend
npm run dev
```

**Expected output:**
```
  VITE v5.0.11  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 5: Test the System

1. Open browser: `http://localhost:3000`
2. You should see the **AI Exam Evaluator** interface
3. Upload 3 PDF files:
   - Question Paper
   - Answer Key
   - Student Answer Sheet (handwritten)
4. Click "Start Evaluation"
5. Watch the progress tracker
6. View results when complete

## 🎯 Test with Sample Data

### Create Test PDFs

You can test with simple text PDFs:

**Question Paper Example:**
```
SECTION A

A1. What is AI? [2 marks]
A2. Define machine learning. [3 marks]
A3. Explain neural networks. [5 marks]

SECTION B

B1. Describe supervised learning. [7 marks]
B2. What is deep learning? [6 marks]
B3. Explain reinforcement learning. [7 marks]

SECTION C

C1. Compare CNN and RNN. [7 marks]
C2. Describe transformers. [6 marks]
C3. Explain attention mechanism. [7 marks]
```

**Answer Key Example:**
```
SECTION A
A1. AI is the simulation of human intelligence in machines. [2 marks]
A2. Machine learning is a subset of AI that enables systems to learn from data. [3 marks]

SECTION B
B1. Supervised learning uses labeled data to train models. [7 marks]
```

**Student Answer Example:**
```
Student ID: 12345

SECTION A
A1. AI is about making smart computers
A2. Machine learning helps computers learn automatically

SECTION B
B1. In supervised learning, we give the computer examples with correct answers
```

## 📊 Verify System Health

### Check Backend Health

```powershell
# In PowerShell or browser
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "ollama_host": "http://localhost:11434",
  "models": {
    "mapping": "qwen2.5:14b",
    "evaluation": "deepseek-r1:7b-qwen-distill-q8_0"
  }
}
```

### Check API Documentation

Open: `http://localhost:8000/docs`

You should see the interactive Swagger UI with all endpoints.

## ⚠️ Common Issues

### Issue: "Model not found"

**Solution:**
```powershell
ollama pull qwen2.5:14b
ollama pull deepseek-r1:7b-qwen-distill-q8_0
```

### Issue: "Port 8000 already in use"

**Solution:**
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: "Poppler not found"

**Solution:**
1. Download: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\poppler`
3. Add `C:\poppler\Library\bin` to PATH
4. Restart PowerShell

### Issue: "OCR API error"

**Solution:**
Verify `.env` file exists with:
```
OCR_API_KEY=K86163544688957
```

### Issue: "Connection refused to Ollama"

**Solution:**
```powershell
# Check if Ollama is running
ollama list

# If not, restart Ollama (it usually starts automatically on Windows)
```

## 🎓 Understanding the Output

### Section Evaluation

Each section shows:
- **Questions Evaluated**: Which questions were attempted
- **Marks Obtained**: Marks awarded per question
- **Dropped Question**: If student answered all 3, the lowest is dropped
- **Feedback**: Constructive feedback for each question

### Overall Performance

- **Total Marks**: Sum of all sections (max 50)
- **Percentage**: (Total / 50) × 100
- **Remarks**: Overall performance assessment

### Example Output

```json
{
  "student_id": "12345",
  "sections": {
    "A": {
      "total_marks_obtained": 8.5,
      "max_marks": 10,
      "dropped_question": null
    }
  },
  "total_marks": 42.0,
  "max_total_marks": 50.0,
  "percentage": 84.0,
  "remarks": "Very good performance with strong conceptual clarity."
}
```

## 📝 Next Steps

1. **Read Full Documentation**: See [README.md](README.md)
2. **Understand Prompts**: See [PROMPTS.md](PROMPTS.md)
3. **Configure Rules**: Edit `backend/app/config/config.yaml`
4. **Test with Real Exams**: Upload actual exam papers

## 🆘 Need Help?

1. Check logs: `backend/logs/app.log`
2. API docs: `http://localhost:8000/docs`
3. Frontend console: Press F12 in browser
4. Backend logs: Check terminal running uvicorn

## ✅ System Ready!

If you see:
- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ Both models loaded in Ollama
- ✅ Can access the UI

**You're ready to evaluate exams! 🎉**

---

**Quick Start Version**: 1.0.0  
**System**: Production Ready  
**Last Updated**: January 2026
