// src/components/UploadForm.js
import React from 'react';

const UploadForm = ({ handleSubmit, isLoading }) => {
  return (
    <article>
      <header>
        <h3>Upload Your Swings</h3>
      </header>
      <form onSubmit={handleSubmit}>
        <div className="grid">
          <label htmlFor="video_dtl">
            Down-the-Line (DTL) Video
            <input type="file" id="video_dtl" name="video_file_dtl" accept="video/*" required disabled={isLoading} />
          </label>
          <label htmlFor="video_fo">
            Face-On (FO) Video
            <input type="file" id="video_fo" name="video_file_fo" accept="video/*" required disabled={isLoading} />
          </label>
        </div>
        <button type="submit" aria-busy={isLoading} disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze Swing'}
        </button>
      </form>
    </article>
  );
};

export default UploadForm;