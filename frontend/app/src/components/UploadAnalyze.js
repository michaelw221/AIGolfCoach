import React, { useState } from 'react';
import { getAuthHeader } from '../services/auth';

export default function UploadAnalyze({ setJobId, setStatus, setError, status, jobId, results }) {
  const[dtlFile, setDtlFile] = useState(null);
  const [foFile, setFoFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!dtlFile || !foFile) {
      setError("Please select both a DTL and Face-On video.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setStatus("Uploading files to server...");

    const formData = new FormData();
    formData.append('video_file_dtl', dtlFile);
    formData.append('video_file_fo', foFile);

    try {
      const response = await fetch('http://localhost:8000/api/swings', {
        method: 'POST',
        headers: getAuthHeader(),
        body: formData
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed');
      
      setJobId(data.id);
    } catch (err) {
      setError(err.message);
      setIsSubmitting(false);
    }
  };

  // --- LOADING SCREEN ---
  if (jobId || isSubmitting) {
    // Read dynamic progress from backend polling, default to 5% during upload
    const progress = results?.progress || 5; 
    const message = results?.message || status;
    const images = results?.debug_images?.fo || results?.debug_images?.dtl || null;

    return (
      <div style={{ textAlign: 'center', marginTop: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ color: 'var(--accent)' }}>Analyzing your swing...</h2>
        
        {/* Dynamic Progress Bar */}
        <div className="progress-container">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <p style={{ color: 'var(--text-main)', fontWeight: '600' }}>{message}</p>

        {/* Image Display */}
        <div className="placeholder-grid" style={{ marginTop: '3rem' }}>
          {images && images.address && images.top && images.impact ? (
            // Render the images once they arrive from the backend
            ['address', 'top', 'impact'].map((phase) => (
              <div key={phase} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <p style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-light)' }}>{phase.toUpperCase()}</p>
                <img 
                  src={`data:image/jpeg;base64,${images[phase]}`} 
                  alt={phase} 
                  style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--border)' }} 
                />
              </div>
            ))
          ) : (
            // Render Grey Box Placeholders while waiting
            <>
              <div className="gray-box"><img src="https://img.icons8.com/ios-glyphs/90/000000/image.png" alt="img" /></div>
              <div className="gray-box"><img src="https://img.icons8.com/ios-glyphs/90/000000/image.png" alt="img" /></div>
              <div className="gray-box"><img src="https://img.icons8.com/ios-glyphs/90/000000/image.png" alt="img" /></div>
            </>
          )}
        </div>
        
        <p style={{ textAlign: 'center', color: 'var(--text-light)', marginTop: '2rem', fontSize: '0.9rem' }}>
          Images above are the pose estimated frames gathered from the videos.<br/>
          (They will appear as soon as the key frames are detected).
        </p>
      </div>
    );
  }

  // --- UPLOAD SCREEN ---
  return (
    <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Upload Your Swing</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="upload-grid">
          <div className="upload-slot">
            <input type="file" accept="video/mp4,video/quicktime" className="file-input" onChange={(e) => setDtlFile(e.target.files[0])} />
            <h3 style={{ color: dtlFile ? 'var(--success)' : 'var(--text-main)' }}>
              {dtlFile ? '✅ ' + dtlFile.name : '📁 DTL Video'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-light)' }}>Click to select Down-the-Line view</p>
          </div>
          
          <div className="upload-slot">
            <input type="file" accept="video/mp4,video/quicktime" className="file-input" onChange={(e) => setFoFile(e.target.files[0])} />
            <h3 style={{ color: foFile ? 'var(--success)' : 'var(--text-main)' }}>
              {foFile ? '✅ ' + foFile.name : '📁 FO Video'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-light)' }}>Click to select Face-On view</p>
          </div>
        </div>
        
        <div style={{ textAlign: 'center' }}>
          <button type="submit" className="btn-accent" style={{ width: '100%', maxWidth: '300px' }} disabled={!dtlFile || !foFile}>
            Run Analysis
          </button>
        </div>
      </form>
    </div>
  );
}