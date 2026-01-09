/**
 * ProgressTracker Component
 * Shows evaluation progress
 */

import React from 'react';

const ProgressTracker = ({ status }) => {
  if (!status) return null;

  const steps = [
    { id: 'initialized', label: 'Initialized', icon: '📝' },
    { id: 'ocr_extraction', label: 'OCR Extraction', icon: '🔍' },
    { id: 'preprocessing', label: 'Preprocessing', icon: '⚙️' },
    { id: 'mapping', label: 'Question Mapping', icon: '🗺️' },
    { id: 'evaluation', label: 'Evaluation', icon: '📊' },
    { id: 'completed', label: 'Completed', icon: '✅' }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === status.current_step);

  return (
    <div className="progress-tracker">
      <div className="progress-header">
        <h3>Processing Status</h3>
        <span className="status-badge status-{status.status}">{status.status}</span>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{ width: `${status.progress_percentage}%` }}
          />
        </div>
        <span className="progress-percentage">{status.progress_percentage.toFixed(0)}%</span>
      </div>

      <div className="steps-container">
        {steps.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step.id}
              className={`step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
            >
              <div className="step-icon">{step.icon}</div>
              <div className="step-label">{step.label}</div>
            </div>
          );
        })}
      </div>

      {status.current_step && (
        <div className="current-step-info">
          <p>Current: <strong>{status.current_step.replace(/_/g, ' ').toUpperCase()}</strong></p>
        </div>
      )}
    </div>
  );
};

export default ProgressTracker;
