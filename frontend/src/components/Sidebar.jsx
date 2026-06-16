import React from 'react';

const Sidebar = ({ documents, sessionId, onReset, sessionReady }) => {
  return (
    <aside className="chat-sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onReset} disabled={!sessionReady}>
          <span className="plus-icon">+</span> New Chat
        </button>
      </div>
      
      <div className="sidebar-content">
        <div className="sidebar-section">
          <h3 className="sidebar-label">DOCUMENTS</h3>
          <div className="document-list">
            {documents.length === 0 ? (
              <p className="no-docs-text">No documents uploaded</p>
            ) : (
              documents.map((doc, idx) => (
                <div key={idx} className="document-item">
                  <span className="doc-icon">📄</span>
                  <div className="doc-info">
                    <span className="doc-name">{doc.name}</span>
                    <span className="doc-chunks">{doc.chunks} chunks</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="avatar">U</div>
          <span className="username">User Session</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
