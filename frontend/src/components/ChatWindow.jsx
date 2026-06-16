import React, { useState, useRef, useEffect } from 'react';

const ChatWindow = ({ messages, onSend, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className="message-wrapper">
              <div className="message-avatar">
                {msg.role === 'assistant' ? '🤖' : 'U'}
              </div>
              <div className="message-content">
                <div className="message-text">{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources-container">
                    <p className="sources-title">Sources:</p>
                    <div className="sources-list">
                      {msg.sources.map((src, sIdx) => (
                        <span key={sIdx} className="source-tag">
                          [{sIdx + 1}] {src.filename || 'Source'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-row assistant">
            <div className="message-wrapper">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <form onSubmit={handleSubmit} className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={disabled ? "Upload a document to start..." : "Ask anything about your documents..."}
            disabled={disabled}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || isLoading || disabled}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </form>
        <p className="input-footer">
          RAG Assistant can make mistakes. Verify important information.
        </p>
      </div>
    </div>
  );
};

export default ChatWindow;
