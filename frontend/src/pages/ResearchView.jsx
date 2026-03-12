import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  HiOutlineArrowLeft,
  HiOutlineDocumentArrowDown,
  HiOutlineExclamationTriangle,
  HiOutlineLink,
  HiOutlineCheck,
} from 'react-icons/hi2';
import { motion, AnimatePresence } from 'framer-motion';
import { useResearchStatus } from '../hooks/useResearchStatus';
import { getResearchReport } from '../services/api';
import ProgressTracker from '../components/ProgressTracker';
import LoadingSpinner from '../components/LoadingSpinner';
import ChatSidebar from '../components/ChatSidebar';
import ReactMarkdown from 'react-markdown';
import { API_BASE_URL } from '../services/api';
import './ResearchView.css';

export default function ResearchView() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const { status, loading, error } = useResearchStatus(taskId);
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    if (status?.status === 'completed' && !report) {
      setReportLoading(true);
      getResearchReport(taskId)
        .then(setReport)
        .catch(console.error)
        .finally(() => setReportLoading(false));
    }
  }, [status?.status, taskId, report]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const handleDownload = () => {
    handleExport('markdown');
  };

  const handleExport = async (type) => {
    try {
      setReportLoading(true);
      const url = `${API_BASE_URL}/research/${taskId}/export/${type}`;
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Download failed');
      
      const data = await response.arrayBuffer();
      
      // Determine extension, filename, and MIME type
      let extension, mimeType;
      if (type === 'pdf') {
        extension = '.pdf';
        mimeType = 'application/pdf';
      } else if (type === 'bibtex') {
        extension = '.bib';
        mimeType = 'application/x-bibtex';
      } else {
        extension = '.md';
        mimeType = 'text/markdown';
      }
      
      const safeTopic = (status?.topic || 'research-report')
        .replace(/[^a-z0-9]/gi, '_')
        .toLowerCase()
        .slice(0, 30);
      const filename = `${safeTopic}_${taskId.slice(0, 8)}${extension}`;
      
      // Create a typed blob with the correct MIME type
      const blob = new Blob([data], { type: mimeType });
      const blobUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
      }, 100);
    } catch (err) {
      console.error('Export error:', err);
      alert('Failed to export report. Please try again.');
    } finally {
      setReportLoading(false);
    }
  };

  if (loading && !status) {
    return <LoadingSpinner size="lg" message="Loading research task..." />;
  }

  if (error && !status) {
    return (
      <div className="error-state">
        <HiOutlineExclamationTriangle className="error-icon" />
        <h2>Task Not Found</h2>
        <p>{error}</p>
        <button className="back-btn" onClick={() => navigate('/')}>
          Go Back
        </button>
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.5, staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="research-view" id="research-view-page">
      {/* Header */}
      <motion.div 
        className="view-header"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <button className="back-link" onClick={() => navigate('/')}>
          <HiOutlineArrowLeft /> Back to Dashboard
        </button>
        <div className="view-title-row">
          <div>
            <h1 className="view-title">{status?.topic}</h1>
            <div className="view-meta">
              <span className={`status-badge status-${status?.status}`}>
                {status?.status}
              </span>
              {status?.papers_found > 0 && (
                <span className="papers-count">
                  {status.papers_found} papers found
                </span>
              )}
            </div>
          </div>
          <div className="header-actions">
            {report && (
              <>
                <button 
                  className="export-btn pdf" 
                  onClick={() => handleExport('pdf')}
                  title="Download Professional PDF"
                >
                  <HiOutlineDocumentArrowDown /> PDF
                </button>
                <button 
                  className="export-btn markdown" 
                  onClick={() => handleExport('markdown')}
                  title="Download Markdown Report"
                >
                  <HiOutlineDocumentArrowDown /> Markdown
                </button>
                <button 
                  className="export-btn bibtex" 
                  onClick={() => handleExport('bibtex')}
                  title="Download BibTeX Citations"
                >
                  <HiOutlineDocumentArrowDown /> BibTeX
                </button>
              </>
            )}
            <button 
              className={`copy-link-btn ${copySuccess ? 'success' : ''}`}
              onClick={handleCopyLink}
              title="Copy shareable report link"
            >
              {copySuccess ? <HiOutlineCheck /> : <HiOutlineLink />}
              {copySuccess ? 'Link Copied!' : 'Share Report'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Progress Tracker / Failed State */}
      <AnimatePresence mode="wait">
        {status?.status !== 'completed' && status?.status !== 'failed' && (
          <motion.div 
            key="progress"
            className="progress-section glass-card"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
          >
            <ProgressTracker
              currentStage={status?.current_stage || 'queued'}
              progress={status?.progress || 0}
              status={status?.status}
            />
          </motion.div>
        )}

        {status?.status === 'failed' && (
          <motion.div 
            key="failed"
            className="failed-card glass-card"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <HiOutlineExclamationTriangle className="failed-icon" />
            <h3>Research Failed</h3>
            <p>An error occurred mapping "{status?.topic}". Please try again.</p>
            <button className="retry-btn" onClick={() => navigate('/')}>
              Try Again
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Report Content */}
      <AnimatePresence>
        {reportLoading && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
          >
            <LoadingSpinner size="md" message="Loading report..." />
          </motion.div>
        )}
      </AnimatePresence>

      {report && (
        <motion.div 
          className="report-container"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Summary */}
          <motion.section className="report-section glass-card" variants={itemVariants}>
            <h2 className="report-section-title">
              <span className="section-emoji">📋</span> Executive Summary
            </h2>
            <div className="report-text">
              <ReactMarkdown>{report.summary}</ReactMarkdown>
            </div>
          </motion.section>

          {/* Key Techniques */}
          {report.key_techniques?.length > 0 && (
            <motion.section className="report-section glass-card" variants={itemVariants}>
              <h2 className="report-section-title">
                <span className="section-emoji">🔑</span> Key Techniques
              </h2>
              <ul className="techniques-list">
                {report.key_techniques.map((tech, i) => (
                  <li key={i} className="technique-item">
                    <span className="technique-dot" />
                    <ReactMarkdown components={{ p: 'span' }}>{tech}</ReactMarkdown>
                  </li>
                ))}
              </ul>
            </motion.section>
          )}

          {/* Comparison Table */}
          {report.comparison_table?.length > 0 && (
            <motion.section className="report-section glass-card" variants={itemVariants}>
              <h2 className="report-section-title">
                <span className="section-emoji">⚖️</span> Comparison Table
              </h2>
              <div className="table-container">
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Method</th>
                      <th>Description</th>
                      <th>Strengths</th>
                      <th>Limitations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.comparison_table.map((row, i) => (
                      <tr key={i}>
                        <td className="method-cell"><ReactMarkdown components={{ p: 'span' }}>{row.method}</ReactMarkdown></td>
                        <td><ReactMarkdown components={{ p: 'span' }}>{row.description}</ReactMarkdown></td>
                        <td className="strength-cell"><ReactMarkdown components={{ p: 'span' }}>{row.strengths}</ReactMarkdown></td>
                        <td className="limitation-cell"><ReactMarkdown components={{ p: 'span' }}>{row.limitations}</ReactMarkdown></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.section>
          )}

          {/* Future Directions */}
          {report.future_directions?.length > 0 && (
            <motion.section className="report-section glass-card" variants={itemVariants}>
              <h2 className="report-section-title">
                <span className="section-emoji">🔮</span> Future Directions
              </h2>
              <ul className="directions-list">
                {report.future_directions.map((dir, i) => (
                  <li key={i} className="direction-item">
                    <span className="direction-number">{i + 1}</span>
                    <div className="direction-text"><ReactMarkdown components={{ p: 'span' }}>{dir}</ReactMarkdown></div>
                  </li>
                ))}
              </ul>
            </motion.section>
          )}

          {/* Analyzed Papers */}
          {report.papers?.length > 0 && (
            <motion.section className="report-section glass-card" variants={itemVariants}>
              <h2 className="report-section-title">
                <span className="section-emoji">📄</span> Analyzed Papers
              </h2>
              <div className="papers-grid">
                {report.papers.map((paper, i) => (
                  <PaperCard key={paper.id || i} paper={paper} />
                ))}
              </div>
            </motion.section>
          )}

          {/* References */}
          {report.references?.length > 0 && (
            <motion.section className="report-section glass-card" variants={itemVariants}>
              <h2 className="report-section-title">
                <span className="section-emoji">📚</span> References
              </h2>
              <ol className="references-list">
                {report.references.map((ref, i) => (
                  <li key={i} className="reference-item">{ref}</li>
                ))}
              </ol>
            </motion.section>
          )}
        </motion.div>
      )}

      {/* Interactive Chat */}
      {status?.status === 'completed' && <ChatSidebar taskId={taskId} />}
    </div>
  );
}

function PaperCard({ paper }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const summary = paper.summary || paper.abstract || '';
  const isLong = summary.length > 450;
  
  const displaySummary = isLong && !isExpanded 
    ? summary.slice(0, 450) + '...' 
    : summary;

  return (
    <motion.div 
      className="paper-card" 
      id={`paper-${paper.id}`}
      whileHover={{ y: -4, shadow: "0 10px 40px rgba(0,0,0,0.3)" }}
    >
      <div className="paper-card-main">
        <div className="paper-header">
          <h4 className="paper-title">{paper.title}</h4>
          {paper.relevance_score != null && paper.relevance_score > 0 && (
            <div className="relevance-container">
              <span className="relevance-label">Relevance</span>
              <span className={`relevance-badge ${paper.relevance_score >= 0.7 ? 'high' : paper.relevance_score >= 0.4 ? 'medium' : 'low'}`}>
                {(paper.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
        
        <p className="paper-authors">
          {(() => {
            if (!paper.authors) return 'Unknown Authors';
            const authors = paper.authors.split(/[,;]| and /);
            if (authors.length > 5) {
              return authors.slice(0, 5).join(', ') + ' et al.';
            }
            return paper.authors;
          })()}
        </p>

        <motion.div 
          className={`paper-summary-content ${isExpanded ? 'expanded' : ''}`}
          initial={false}
          animate={{ height: isExpanded ? 'auto' : '120px' }}
        >
          <ReactMarkdown>{isExpanded ? summary : displaySummary}</ReactMarkdown>
        </motion.div>

        <div className="paper-card-footer">
          <div className="footer-links">
            <a href={paper.url} target="_blank" rel="noopener noreferrer" className="paper-link-btn">
              View Source
            </a>
            {isLong && (
              <button 
                className="read-more-btn"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? 'Show Less' : 'Read Full Summary'}
              </button>
            )}
          </div>
          <span className="paper-source-tag">{paper.source || 'Scholar'}</span>
        </div>
      </div>
    </motion.div>
  );
}
