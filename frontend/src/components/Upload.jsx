import React, { useState, useRef } from 'react';

function Upload({ onAnalysis, loading, error }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [dragOver, setDragOver] = useState(null); // 'resume' | 'jd'
  const resumeRef = useRef();
  const jdRef = useRef();

  const handleDrop = (e, type) => {
    e.preventDefault();
    setDragOver(null);
    const file = e.dataTransfer.files[0];
    if (!file) return;
    if (type === 'resume') setResumeFile(file);
    else setJdFile(file);
  };

  const handleSubmit = () => {
    if (resumeFile && jdFile) onAnalysis(resumeFile, jdFile);
  };

  const DropZone = ({ type, file, setFile, inputRef, label, icon }) => (
    <div
      className={`dropzone ${dragOver === type ? 'dragover' : ''} ${file ? 'has-file' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(type); }}
      onDragLeave={() => setDragOver(null)}
      onDrop={(e) => handleDrop(e, type)}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        style={{ display: 'none' }}
        onChange={(e) => setFile(e.target.files[0])}
        disabled={loading}
      />
      <div className="dropzone-icon">{file ? '✓' : icon}</div>
      <div className="dropzone-label">{file ? file.name : label}</div>
      <div className="dropzone-sub">
        {file ? 'Click to replace' : 'PDF, DOCX, or TXT · Click or drag'}
      </div>
    </div>
  );

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <div className="hero-eyebrow">AI-Powered Resume Analysis</div>
        <h1 className="hero-title">
          Know exactly where<br />
          <span className="hero-accent">you stand.</span>
        </h1>
        <p className="hero-sub">
          Upload your resume and a job description. Get your match score,
          skill gaps, and personalized interview questions in seconds.
        </p>
      </div>

      <div className="upload-card">
        <div className="upload-grid">
          <DropZone
            type="resume"
            file={resumeFile}
            setFile={setResumeFile}
            inputRef={resumeRef}
            label="Drop your resume here"
            icon="📄"
          />
          <div className="upload-vs">vs</div>
          <DropZone
            type="jd"
            file={jdFile}
            setFile={setJdFile}
            inputRef={jdRef}
            label="Drop the job description"
            icon="📋"
          />
        </div>

        {error && (
          <div className="upload-error">
            <span>⚠</span> {error}
          </div>
        )}

        <button
          className={`analyze-btn ${loading ? 'loading' : ''}`}
          onClick={handleSubmit}
          disabled={loading || !resumeFile || !jdFile}
        >
          {loading ? (
            <span className="btn-loading">
              <span className="spinner" />
              Analyzing your profile…
            </span>
          ) : (
            'Analyze match →'
          )}
        </button>

        <p className="upload-note">Files are processed locally and never stored permanently.</p>
      </div>
    </div>
  );
}

export default Upload;
