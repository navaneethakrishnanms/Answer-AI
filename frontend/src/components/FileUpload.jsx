/**
 * FileUpload Component
 * Handles PDF file uploads with drag-and-drop
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

const FileUpload = ({ label, onFileSelect, selectedFile, id }) => {
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError('');

    if (rejectedFiles.length > 0) {
      setError('Please upload a PDF file');
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    multiple: false
  });

  return (
    <div className="file-upload">
      <label className="file-upload-label">{label}</label>
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
      >
        <input {...getInputProps()} id={id} />
        {selectedFile ? (
          <div className="file-info">
            <span className="file-icon">📄</span>
            <span className="file-name">{selectedFile.name}</span>
            <span className="file-size">({(selectedFile.size / 1024).toFixed(2)} KB)</span>
          </div>
        ) : (
          <div className="dropzone-prompt">
            {isDragActive ? (
              <p>Drop the PDF file here...</p>
            ) : (
              <>
                <p>📎 Drag & drop PDF file here</p>
                <p className="or-text">or</p>
                <button type="button" className="browse-button">Browse Files</button>
              </>
            )}
          </div>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default FileUpload;
