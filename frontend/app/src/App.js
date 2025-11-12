// src/App.js
import React, { useState } from 'react';
import UploadForm from './components/uploadForm';
import ResultsDisplay from './components/resultsDisplay';
import LoadingSpinner from './components/loadingSpinner';
import './App.css';

function App() {
  const [status, setStatus] = useState('Ready to analyze. Please upload both video files.');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // New state for loading

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    setIsLoading(true); // Start loading
    setStatus('Uploading and processing...');
    setResults(null);
    setError(null);

    const formData = new FormData(event.currentTarget);
    const apiUrl = 'http://127.0.0.1:8000/api/swings';

    try {
      const response = await fetch(apiUrl, { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'An unknown error occurred.');
      
      setStatus('Analysis complete!');
      setResults(data);
    } catch (err) {
      setStatus('An error occurred during analysis.');
      setError(err.message);
    } finally {
      setIsLoading(false); // Stop loading, regardless of success or failure
    }
  };

  return (
    <main className="container">
      <nav>
        <ul><li><strong>AI Golf Coach</strong></li></ul>
        <ul><li>Prototype</li></ul>
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