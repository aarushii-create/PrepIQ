import React, { useState } from 'react';
import Upload from './components/Upload';
import Results from './components/Results';
import './App.css';

function App() {
  const [page, setPage] = useState('upload'); // 'upload' | 'results'
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalysis = async (resumeFile, jobDescriptionFile) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('job_description', jobDescriptionFile);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Analysis failed');

      const data = await response.json();
      setAnalysisResult(data);
      setPage('results');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setAnalysisResult(null);
    setError(null);
    setPage('upload');
  };

  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-inner">
          <div className="nav-brand" onClick={handleNewAnalysis} style={{ cursor: 'pointer' }}>
            <span className="nav-logo">⬡</span>
            <span className="nav-title">PrepIQ</span>
          </div>
          <div className="nav-steps">
            <span className={`nav-step ${page === 'upload' ? 'active' : page === 'results' ? 'done' : ''}`}>
              01 Upload
            </span>
            <span className="nav-step-divider">—</span>
            <span className={`nav-step ${page === 'results' ? 'active' : ''}`}>
              02 Results
            </span>
          </div>
        </div>
      </nav>

      <main className="main">
        {page === 'upload' ? (
          <Upload onAnalysis={handleAnalysis} loading={loading} error={error} />
        ) : (
          <Results result={analysisResult} onNewAnalysis={handleNewAnalysis} />
        )}
      </main>
    </div>
  );
}

export default App;
