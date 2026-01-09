/**
 * API Service for AI Exam Evaluator
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Upload PDF files for evaluation
 * @param {File} questionPaper - Question paper PDF
 * @param {File} answerKey - Answer key PDF
 * @param {File} studentAnswers - Student answers PDF
 * @returns {Promise} - Upload response with job_id
 */
export const uploadFiles = async (questionPaper, answerKey, studentAnswers) => {
  const formData = new FormData();
  formData.append('question_paper', questionPaper);
  formData.append('answer_key', answerKey);
  formData.append('student_answers', studentAnswers);

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data;
};

/**
 * Get status of an evaluation job
 * @param {string} jobId - Job identifier
 * @returns {Promise} - Job status
 */
export const getJobStatus = async (jobId) => {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
};

/**
 * Get evaluation result
 * @param {string} jobId - Job identifier
 * @param {boolean} includeMapping - Include mapping data
 * @returns {Promise} - Evaluation result
 */
export const getResult = async (jobId, includeMapping = false) => {
  const response = await api.get(`/api/result/${jobId}`, {
    params: { include_mapping: includeMapping }
  });
  return response.data;
};

/**
 * Download evaluation result as JSON
 * @param {string} jobId - Job identifier
 * @returns {Promise} - Download blob
 */
export const downloadResult = async (jobId) => {
  const response = await api.get(`/api/result/${jobId}/download`, {
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Poll job status until completion
 * @param {string} jobId - Job identifier
 * @param {function} onProgress - Progress callback
 * @param {number} interval - Polling interval in ms
 * @returns {Promise} - Final status
 */
export const pollJobStatus = async (jobId, onProgress, interval = 2000) => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getJobStatus(jobId);
        
        if (onProgress) {
          onProgress(status);
        }

        if (status.status === 'completed') {
          resolve(status);
        } else if (status.status === 'failed') {
          reject(new Error(status.error?.message || 'Evaluation failed'));
        } else {
          setTimeout(poll, interval);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
};

export default api;
