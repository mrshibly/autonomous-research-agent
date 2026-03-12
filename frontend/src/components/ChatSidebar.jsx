import React, { useState, useRef, useEffect } from 'react';
import { 
  HiOutlineChatBubbleLeftRight, 
  HiOutlineXMark, 
  HiOutlinePaperAirplane,
  HiOutlineTrash
} from 'react-icons/hi2';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { chatWithResearch } from '../services/api';
import './ChatSidebar.css';

export default function ChatSidebar({ taskId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState(() => {
    // Load chat history from local storage
    const saved = localStorage.getItem(`chat_${taskId}`);
    return saved ? JSON.parse(saved) : [];
  });
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    // Save chat history to local storage
    localStorage.setItem(`chat_${taskId}`, JSON.stringify(chatHistory));
  }, [chatHistory, taskId]);

  const handleClearChat = () => {
    if (window.confirm('Clear chat history?')) {
      setChatHistory([]);
      localStorage.removeItem(`chat_${taskId}`);
    }
  };

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
      
      if (err.response?.data?.detail) {
        displayError = err.response.data.detail;
      } else if (err.message?.includes('429')) {
        displayError = 'Rate limit exceeded. Please wait a moment.';
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
      <AnimatePresence>
        {!isOpen && (
          <motion.button 
            className="chat-toggle-btn"
            onClick={() => setIsOpen(true)}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <HiOutlineChatBubbleLeftRight />
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            className="chat-sidebar"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          >
            <div className="chat-header">
              <div className="chat-title">
                <HiOutlineChatBubbleLeftRight className="chat-icon" />
                <h3>Research Assistant</h3>
              </div>
              <div className="chat-header-actions">
                {chatHistory.length > 0 && (
                  <button className="chat-clear-btn" onClick={handleClearChat} title="Clear Chat">
                    <HiOutlineTrash />
                  </button>
                )}
                <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
                  <HiOutlineXMark />
                </button>
              </div>
            </div>

            <div className="chat-messages">
              {chatHistory.length === 0 && (
                <div className="chat-empty">
                  <div className="empty-icon-ring">
                    <HiOutlineChatBubbleLeftRight />
                  </div>
                  <p>Ask anything about the researched papers!</p>
                  <div className="chat-suggestions">
                    <button onClick={() => setMessage("What are the key findings?")}>"What are the key findings?"</button>
                    <button onClick={() => setMessage("Are there any conflicting views?")}>"Are there any conflicting views?"</button>
                  </div>
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <motion.div 
                  key={i} 
                  className={`chat-bubble ${msg.role}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="chat-content">
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.sources?.length > 0 && (
                    <div className="chat-sources">
                      <span className="sources-label">Sources:</span>
                      {msg.sources.map((s, j) => (
                        <span key={j} className="chat-source-tag" title={s.paper_title}>
                          [{j + 1}]
                        </span>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
              {loading && (
                <motion.div 
                  className="chat-bubble assistant loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                </motion.div>
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
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
