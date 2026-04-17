import React, { useState, useEffect } from 'react';
import './App.css';
import { getToken, removeToken, getAuthHeader } from './services/auth';
import UserAuth from './components/userAuth';
import UploadAnalyze from './components/UploadAnalyze';
import ResultsView from './components/ResultsView';
import HistoryView from './components/HistoryView';
import DashboardView from './components/DashboardView';

const UserIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

function App() {
  const [view, setView] = useState('landing'); 
  const[isAuth, setIsAuth] = useState(!!getToken());
  const [showDropdown, setShowDropdown] = useState(false);
  
  // App State
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleLogout = () => {
    removeToken();
    setIsAuth(false);
    setShowDropdown(false);
    setView('landing');
  };

  // --- API Polling Logic ---
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
          setView('results');
          setJobId(null);
          clearInterval(intervalId);
        } else if (data.status === 'failed') {
          setError(data.error_message || "A technical error occurred.");
          setStatus('Analysis failed.');
          setJobId(null);
          clearInterval(intervalId);
        } else {
          if (data.analysis_results && data.analysis_results.progress) {
            setResults(data.analysis_results);
            setStatus(data.analysis_results.message); 
          } else {
            setStatus(`Processing... (${data.status})`);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => clearInterval(intervalId);
  },[jobId]);

  return (
    <div>
      <nav className="navbar">
        <div className="nav-logo" onClick={() => setView('landing')}>AI Golf Coach</div>
        
        <div className="nav-actions">
          {(view !== 'auth' && view !== 'landing') && (
            <button className="btn-dark" onClick={() => { setView('analyze'); setResults(null); setError(null); }}>
              New Analysis
            </button>
          )}

          {isAuth ? (
            // LOGGED IN: Show User Icon with Dropdown
            <div className="nav-dropdown-btn icon-btn" onClick={() => setShowDropdown(!showDropdown)}>
              <UserIcon />
              
              {showDropdown && (
                <ul className="dropdown-menu">
                  <li onClick={() => { setView('dashboard'); setShowDropdown(false); }}>Account</li>
                  <li onClick={() => { setView('history'); setShowDropdown(false); }}>History</li>
                  <li onClick={handleLogout} style={{ color: 'var(--error)' }}>Logout</li>
                </ul>
              )}
            </div>
          ) : (
            // LOGGED OUT: Show simple button
            view !== 'auth' && (
              <button className="btn-outline" onClick={() => setView('auth')}>
                Login / Register
              </button>
            )
          )}
        </div>
      </nav>

      <div className="page-container">
        {/* Error Banner */}
        {error && (
          <div style={{ padding: '1rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '8px', marginBottom: '1rem' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {view === 'landing' && (
          <div style={{ textAlign: 'center', marginTop: '10vh' }}>
            <div className="card" style={{ maxWidth: '600px', margin: '0 auto 2rem auto', padding: '4rem 2rem' }}>
              <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: 'var(--primary)' }}>Welcome to your<br/>AI Golf Coach</h1>
              <p style={{ color: 'var(--text-light)', marginBottom: '2rem' }}>Upload your swing and get instant biomechanical feedback.</p>
              <button className="btn-accent" style={{ fontSize: '1.2rem', padding: '1rem 3rem' }} onClick={() => setView('analyze')}>
                Run Analysis
              </button>
            </div>
            {!isAuth && <p style={{ color: 'var(--text-light)' }}>Want to save your history? <a href="#" onClick={(e) => {e.preventDefault(); setView('auth');}}>Create an account</a></p>}
          </div>
        )}

        {view === 'auth' && <UserAuth onLogin={() => { setIsAuth(true); setView('analyze'); }} />}
        
        {view === 'analyze' && <UploadAnalyze setJobId={setJobId} setStatus={setStatus} setError={setError} status={status} jobId={jobId} results={results} />}
        
        {view === 'results' && <ResultsView results={results} />}

        {view === 'history' && (
          <HistoryView 
            onViewResults={(savedResults) => {
              setResults(savedResults);
              setError(null);
              setView('results');
            }}
          />
        )}

        {view === 'dashboard' && <DashboardView isActive={view === 'dashboard'} />}
      </div>
    </div>
  );
}

export default App;