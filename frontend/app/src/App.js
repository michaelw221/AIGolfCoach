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

  // --- NEW: Polling Logic ---
  useEffect(() => {
    // If there is no task ID, do nothing
    if (!taskId) return;

    // Set up a timer to check status every 2 seconds
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/swings/${taskId}`);
        const data = await response.json();

        console.log("Polling status:", data.status); // Debugging log

        if (data.status === 'completed') {
            // Job is done!
            setResults(data.result); // Get the inner result object
            setStatus('Analysis complete!');
            setIsLoading(false);
            setTaskId(null); // Stop polling
        } else if (data.status === 'failed') {
            // Job failed
            setError(data.error);
            setStatus('Analysis failed.');
            setIsLoading(false);
            setTaskId(null); // Stop polling
        } else {
            // Job is still 'pending' or 'processing'
            setStatus(`Processing... (Status: ${data.status})`);
        }
      } catch (err) {
        console.error("Polling error:", err);
        // We don't stop polling for network blips, just log it
      }
    }, 2000); // 2000ms = 2 seconds

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