/**
 * Main App Component
 */

import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ProgressTracker from './components/ProgressTracker';
import ResultsViewer from './components/ResultsViewer';
import {
  uploadFiles,
  pollJobStatus,
  getResult,
  downloadResult
} from './services/api';
import './App.css';

function App() {
  // File states
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerKey, setAnswerKey] = useState(null);
  const [studentAnswers, setStudentAnswers] = useState(null);

  // Processing states
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setStatus(null);

    // Validate files
    if (!questionPaper || !answerKey || !studentAnswers) {
      setError('Please upload all three PDF files');
      return;
    }

    setIsProcessing(true);

    try {
      // Upload files
      const uploadResponse = await uploadFiles(
        questionPaper,
        answerKey,
        studentAnswers
      );

      const newJobId = uploadResponse.job_id;
      setJobId(newJobId);

      // Poll for status updates
      await pollJobStatus(newJobId, (statusUpdate) => {
        setStatus(statusUpdate);
      });

      // Get final result
      const resultData = await getResult(newJobId);
      setResult(resultData);

    } catch (err) {
      console.error('Evaluation error:', err);
      setError(err.message || 'An error occurred during evaluation');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;

    try {
      const blob = await downloadResult(jobId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evaluation_${jobId}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download error:', err);
      setError('Failed to download result');
    }
  };

  const handleReset = () => {
    setQuestionPaper(null);
    setAnswerKey(null);
    setStudentAnswers(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setJobId(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎓 AI Exam Evaluator</h1>
        <p>Production-ready AI-powered handwritten exam evaluation system</p>
      </header>

      <main className="app-main">
        {!result ? (
          <div className="upload-section">
            <form onSubmit={handleSubmit} className="upload-form">
              <FileUpload
                label="📄 Question Paper PDF"
                onFileSelect={setQuestionPaper}
                selectedFile={questionPaper}
                id="question-paper"
              />

              <FileUpload
                label="📋 Answer Key PDF"
                onFileSelect={setAnswerKey}
                selectedFile={answerKey}
                id="answer-key"
              />

              <FileUpload
                label="✍️ Student Answer Sheet PDF (Handwritten)"
                onFileSelect={setStudentAnswers}
                selectedFile={studentAnswers}
                id="student-answers"
              />

              {error && (
                <div className="error-banner">
                  <span className="error-icon">❌</span>
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                className="submit-button"
                disabled={isProcessing || !questionPaper || !answerKey || !studentAnswers}
              >
                {isProcessing ? '⏳ Processing...' : '🚀 Start Evaluation'}
              </button>
            </form>

            {isProcessing && status && (
              <ProgressTracker status={status} />
            )}
          </div>
        ) : (
          <div className="results-section">
            <ResultsViewer result={result} onDownload={handleDownload} />
            <button onClick={handleReset} className="reset-button">
              🔄 Evaluate Another Exam
            </button>
          </div>
        )}

        <div className="info-section">
          <h3>ℹ️ System Information</h3>
          <ul>
            <li>✅ Uses OCR.Space API for handwriting recognition</li>
            <li>✅ Qwen 2.5 (14B) for question-answer mapping</li>
            <li>✅ DeepSeek-R1 for fair and liberal evaluation</li>
            <li>✅ Supports 3 sections (A, B, C) with auto-drop lowest score</li>
            <li>✅ Strict evaluation for 1-mark questions, Liberal for multi-mark</li>
          </ul>
        </div>
      </main>

      <footer className="app-footer">
        <p>© 2026 AI Exam Evaluator - Production System v1.0.0</p>
      </footer>
    </div>
  );
}

export default App;
