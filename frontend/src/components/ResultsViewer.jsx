/**
 * ResultsViewer Component
 * Displays evaluation results
 */

import React, { useState } from 'react';

const ResultsViewer = ({ result, onDownload }) => {
  const [showJson, setShowJson] = useState(false);

  if (!result || !result.evaluation) return null;

  const { evaluation } = result;

  return (
    <div className="results-viewer">
      <div className="results-header">
        <h2>Evaluation Results</h2>
        <div className="results-actions">
          <button
            onClick={() => setShowJson(!showJson)}
            className="toggle-json-button"
          >
            {showJson ? '📊 Show Summary' : '🔍 Show JSON'}
          </button>
          <button onClick={onDownload} className="download-button">
            💾 Download JSON
          </button>
        </div>
      </div>

      {showJson ? (
        <div className="json-viewer">
          <pre>{JSON.stringify(evaluation, null, 2)}</pre>
        </div>
      ) : (
        <div className="results-summary">
          {/* Overall Summary */}
          <div className="summary-card overall">
            <h3>Overall Performance</h3>
            <div className="score-display">
              <div className="score-main">
                <span className="score-value">{evaluation.total_marks}</span>
                <span className="score-separator">/</span>
                <span className="score-max">{evaluation.max_total_marks}</span>
              </div>
              <div className="score-percentage">{evaluation.percentage}%</div>
            </div>
            <div className="remarks">{evaluation.remarks}</div>
            {evaluation.student_id && (
              <div className="student-id">Student ID: {evaluation.student_id}</div>
            )}
          </div>

          {/* Section-wise Results */}
          <div className="sections-results">
            <h3>Section-wise Performance</h3>
            {Object.entries(evaluation.sections).map(([sectionId, section]) => (
              <div key={sectionId} className="section-card">
                <div className="section-header">
                  <h4>Section {sectionId}</h4>
                  <div className="section-score">
                    {section.total_marks_obtained} / {section.max_marks}
                  </div>
                </div>

                {section.dropped_question && (
                  <div className="dropped-info">
                    ℹ️ Question {section.dropped_question} was dropped (lowest score)
                  </div>
                )}

                <div className="questions-list">
                  {section.questions_evaluated.map((question) => (
                    <div
                      key={question.question_ref}
                      className={`question-result ${question.dropped ? 'dropped' : ''}`}
                    >
                      <div className="question-header">
                        <span className="question-ref">{question.question_ref}</span>
                        <span className="question-marks">
                          {question.marks_obtained} / {question.max_marks}
                          {question.dropped && ' (Dropped)'}
                        </span>
                      </div>
                      <div className="question-feedback">{question.feedback}</div>
                      {question.subdivisions && question.subdivisions.length > 0 && (
                        <div className="subdivisions">
                          {question.subdivisions.map((sub) => (
                            <div key={sub.subdivision_ref} className="subdivision-result">
                              <span className="subdivision-ref">{sub.subdivision_ref}:</span>
                              <span className="subdivision-marks">
                                {sub.marks_obtained} / {sub.max_marks}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {section.remarks && (
                  <div className="section-remarks">{section.remarks}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsViewer;
