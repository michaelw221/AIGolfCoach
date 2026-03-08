// src/App.js
import React, { useState, useEffect } from 'react';
import UploadForm from './components/uploadForm';
import ResultsDisplay from './components/resultsDisplay';
import LoadingSpinner from './components/loadingSpinner';
import { getToken, removeToken, getAuthHeader } from './services/auth';
import UserAuth from './components/userAuth';
import History from './components/history';
import './App.css';

function App() {
  const [status, setStatus] = useState('Ready to analyze. Please upload both video files.');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuth, setIsAuth] = useState(!!getToken());
  const [view, setView] = useState('upload'); // 'upload' or 'history'
  const [results, setResults] = useState(null);
  const [jobId, setJobId] = useState(null);

  const handleLogout = () => {
    removeToken();
    setIsAuth(false);
    setResults(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setResults(null);
    setStatus('Uploading and queuing...');

    const formData = new FormData(event.currentTarget);
    
    try {
      const response = await fetch('http://localhost:8000/api/swings', {
        method: 'POST',
        headers: getAuthHeader(),
        body: formData 
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed');
      
      setJobId(data.id);
      setStatus('Upload complete. Processing in background...');
    } catch (err) { 
      setError(err.message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/swings/${jobId}`, {
          headers: getAuthHeader()
        });
        const data = await response.json();

        if (data.status === 'complete') {
          setResults(data.analysis_results); 
          setStatus('Analysis complete!');
          setIsLoading(false);
          setJobId(null);
          clearInterval(intervalId);
        } else if (data.status === 'failed') {
          setError(data.error_message || "A technical error occurred.");
          setStatus('Analysis failed.');
          setIsLoading(false);
          setJobId(null);
          clearInterval(intervalId);
        } else {
          setStatus(`Processing... (Status: ${data.status})`);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => clearInterval(intervalId);
  }, [jobId]);

  if (!isAuth) return <UserAuth onLoginSuccess={() => setIsAuth(true)} />;

  return (
    <main className="container">
      <nav>
        <ul><li><strong>AI Golf Coach</strong></li></ul>
        <ul>
          <li><button className="contrast" onClick={() => {setView('upload'); setResults(null); setError(null);}}>New Analysis</button></li>
          <li><button className="secondary" onClick={() => setView('history')}>History</button></li>
          <li><button className="outline" onClick={handleLogout}>Logout</button></li>
        </ul>
      </nav>

      {view === 'upload' ? (
        <>
          {!results && !isLoading && <UploadForm handleSubmit={handleSubmit} isLoading={isLoading} />}
          
          {isLoading && <LoadingSpinner status={status} />}
          
          {(results || error) && (
            <ResultsDisplay status={status} results={results} error={error} />
          )}
        </>
      ) : (
        <History onSelectJob={(id) => { 
          setJobId(id); 
          setIsLoading(true); // Trigger loading while it fetches the history item
          setView('upload'); 
        }} />
      )}
    </main>
  );
}

export default App;