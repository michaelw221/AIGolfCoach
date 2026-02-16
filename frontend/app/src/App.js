// src/App.js
import React, { useState, useEffect } from 'react';
import UploadForm from './components/uploadForm';
import ResultsDisplay from './components/resultsDisplay';
import LoadingSpinner from './components/loadingSpinner';
import './App.css';

function App() {
  const [status, setStatus] = useState('Ready to analyze. Please upload both video files.');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState(null); // NEW: Store the Task ID

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    setIsLoading(true);
    setStatus('Uploading and queuing...');
    setResults(null);
    setError(null);
    setTaskId(null); // Reset task ID

    const formData = new FormData(event.currentTarget);
    const apiUrl = 'http://localhost:8000/api/swings';

    try {
      // 1. Send the file to start the job
      const response = await fetch(apiUrl, { method: 'POST', body: formData });
      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || 'An unknown error occurred.');
      
      // 2. Save the Task ID to start polling
      setTaskId(data.task_id);
      setStatus('Upload complete. Processing in background...');

    } catch (err) {
      setStatus('An error occurred during upload.');
      setError(err.message);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // If there is no task ID, do nothing
    if (!taskId) return;

    const intervalId = setInterval(async () => {
  try {
    const response = await fetch(`http://localhost:8000/api/swings/${taskId}`);
    const data = await response.json();

    if (data.status === 'completed') {
      if (data.result && data.result.error) {
        setError(data.result.error); // This will be "Invalid Camera Angle..."
        setStatus('Analysis failed.');
      } else {
        setResults(data.result); // This is the healthy biomechanics data
        setStatus('Analysis complete!');
      }
      
      setIsLoading(false);
      setTaskId(null); // Stop polling

    } else if (data.status === 'failed') {
      // This handles a hard crash (e.g., out of memory, code error)
      setError(data.error || "A technical error occurred in the AI worker.");
      setStatus('Technical failure.');
      setIsLoading(false);
      setTaskId(null);
    } else {
      setStatus(`Processing... (Status: ${data.status})`);
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}, 2000);

    // Cleanup: Stop the timer if the component unmounts or taskId changes
    return () => clearInterval(intervalId);
  }, [taskId]);

  return (
    <main className="container">
      <nav>
        <ul><li><strong>AI Golf Coach</strong></li></ul>
        <ul><li>Async Prototype</li></ul>
      </nav>

      <UploadForm handleSubmit={handleSubmit} isLoading={isLoading} />
      
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <ResultsDisplay status={status} results={results} error={error} />
      )}
      
    </main>
  );
}

export default App;