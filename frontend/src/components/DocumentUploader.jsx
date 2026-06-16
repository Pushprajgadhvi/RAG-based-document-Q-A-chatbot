import React, { useRef } from 'react';

const DocumentUploader = ({ onUpload, isLoading, disabled }) => {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="document-uploader">
      <div className="upload-zone" onClick={() => !isLoading && !disabled && fileInputRef.current.click()}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
        />
        <div className="upload-icon">📁</div>
        <h3>{isLoading ? 'Processing...' : 'Click to upload document'}</h3>
        <p>PDF, DOCX, or TXT (Max 10MB)</p>
      </div>
    </div>
  );
};

export default DocumentUploader;
