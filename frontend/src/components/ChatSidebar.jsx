import React, { useState, useRef, useEffect } from 'react';
import { HiOutlineChatBubbleLeftRight, HiOutlineXMark, HiOutlinePaperAirplane } from 'react-icons/hi2';
import { chatWithResearch } from '../services/api';
import './ChatSidebar.css';

export default function ChatSidebar({ taskId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMessage = { role: 'user', content: message };
    setChatHistory(prev => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const response = await chatWithResearch(taskId, message);
      const aiMessage = { 
        role: 'assistant', 
        content: response.answer,
        sources: response.sources 
      };
      setChatHistory(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      let displayError = 'Failed to get answer. Please try again.';
      
      // If we have a specific error message from the backend, use it
      if (err.response?.data?.detail) {
        displayError = err.response.data.detail;
      } else if (err.message) {
        if (err.message.includes('429')) {
          displayError = 'Rate limit exceeded (Groq/OpenAI). Please wait a moment.';
        } else if (err.message.includes('404')) {
          displayError = 'Chat context not found. This research data was likely cleared after the last update.';
        }
      }
      
      setChatHistory(prev => [...prev, { 
        role: 'system', 
        content: displayError 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Toggle Button */}
      <button 
        className={`chat-toggle-btn ${isOpen ? 'hidden' : ''}`}
        onClick={() => setIsOpen(true)}
        title="Chat with Research"
      >
        <HiOutlineChatBubbleLeftRight />
      </button>

      {/* Sidebar Panel */}
      <div className={`chat-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="chat-header">
          <div className="chat-title">
            <HiOutlineChatBubbleLeftRight className="chat-icon" />
            <h3>Research Assistant</h3>
          </div>
          <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
            <HiOutlineXMark />
          </button>
        </div>

        <div className="chat-messages">
          {chatHistory.length === 0 && (
            <div className="chat-empty">
              <p>Ask anything about the researched papers!</p>
              <div className="chat-suggestions">
                <button onClick={() => setMessage("What are the key findings?")}>"What are the key findings?"</button>
                <button onClick={() => setMessage("Are there any conflicting views?")}>"Are there any conflicting views?"</button>
              </div>
            </div>
          )}
          {chatHistory.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              <div className="chat-content">{msg.content}</div>
              {msg.sources?.length > 0 && (
                <div className="chat-sources">
                  {msg.sources.map((s, j) => (
                    <span key={j} className="chat-source-tag" title={s.paper_title}>
                      [{j + 1}]
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant loading">
              <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-area" onSubmit={handleSendMessage}>
          <input 
            type="text" 
            placeholder="Ask a question..." 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !message.trim()}>
            <HiOutlinePaperAirplane />
          </button>
        </form>
      </div>
    </>
  );
}
