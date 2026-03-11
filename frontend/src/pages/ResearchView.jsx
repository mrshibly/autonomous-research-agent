import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  HiOutlineArrowLeft,
  HiOutlineDocumentArrowDown,
  HiOutlineExclamationTriangle,
} from 'react-icons/hi2';
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

  useEffect(() => {
    if (status?.status === 'completed' && !report) {
      setReportLoading(true);
      getResearchReport(taskId)
        .then(setReport)
        .catch(console.error)
        .finally(() => setReportLoading(false));
    }
  }, [status?.status, taskId, report]);

  const handleDownload = () => {
    handleExport('markdown');
  };

  const handleExport = async (type) => {
    try {
      setReportLoading(true);
      const url = `${API_BASE_URL}/research/${taskId}/export/${type}`;
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Determine extension and filename
      const extension = type === 'pdf' ? '.pdf' : type === 'bibtex' ? '.bib' : '.md';
      const safeTopic = (status?.topic || 'research-report')
        .replace(/[^a-z0-9]/gi, '_')
        .toLowerCase()
        .slice(0, 30);
      const filename = `${safeTopic}_${taskId.slice(0, 8)}${extension}`;
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
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

  return (
    <div className="research-view" id="research-view-page">
      {/* Header */}
      <div className="view-header animate-fade-in-up">
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
          {report && (
            <div className="export-actions">
              <button 
                className="download-btn secondary" 
                onClick={() => handleExport('pdf')}
                title="Download PDF"
              >
                <HiOutlineDocumentArrowDown /> PDF
              </button>
              <button 
                className="download-btn secondary" 
                onClick={() => handleExport('bibtex')}
                title="Download BibTeX"
              >
                <HiOutlineDocumentArrowDown /> BibTeX
              </button>
              <button className="download-btn" onClick={handleDownload} id="download-report-btn">
                <HiOutlineDocumentArrowDown />
                Markdown
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Progress Tracker / Failed State */}
      {status?.status !== 'completed' && status?.status !== 'failed' && (
        <div className="progress-section glass-card animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <ProgressTracker
            currentStage={status?.current_stage || 'queued'}
            progress={status?.progress || 0}
            status={status?.status}
          />
        </div>
      )}

      {status?.status === 'failed' && (
        <div className="failed-card glass-card animate-fade-in-up">
          <HiOutlineExclamationTriangle className="failed-icon" />
          <h3>Research Failed</h3>
          <p>An error occurred mapping "{status?.topic}". Please try again.</p>
          <button className="retry-btn" onClick={() => navigate('/')}>
            Try Again
          </button>
        </div>
      )}

      {/* Report Content */}
      {reportLoading && (
        <LoadingSpinner size="md" message="Loading report..." />
      )}

      {report && (
        <div className="report-container animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          {/* Summary */}
          <section className="report-section glass-card">
            <h2 className="report-section-title">
              <span className="section-emoji">📋</span> Executive Summary
            </h2>
            <div className="report-text">
              <ReactMarkdown>{report.summary}</ReactMarkdown>
            </div>
          </section>

          {/* Key Techniques */}
          {report.key_techniques?.length > 0 && (
            <section className="report-section glass-card" style={{ animationDelay: '0.3s' }}>
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
            </section>
          )}

          {/* Comparison Table */}
          {report.comparison_table?.length > 0 && (
            <section className="report-section glass-card" style={{ animationDelay: '0.4s' }}>
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
            </section>
          )}

          {/* Future Directions */}
          {report.future_directions?.length > 0 && (
            <section className="report-section glass-card" style={{ animationDelay: '0.5s' }}>
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
            </section>
          )}

          {/* Analyzed Papers */}
          {report.papers?.length > 0 && (
            <section className="report-section glass-card" style={{ animationDelay: '0.55s' }}>
              <h2 className="report-section-title">
                <span className="section-emoji">📄</span> Analyzed Papers
              </h2>
              <div className="papers-grid">
                {report.papers.map((paper, i) => (
                  <PaperCard key={paper.id || i} paper={paper} />
                ))}
              </div>
            </section>
          )}

          {/* References */}
          {report.references?.length > 0 && (
            <section className="report-section glass-card" style={{ animationDelay: '0.6s' }}>
              <h2 className="report-section-title">
                <span className="section-emoji">📚</span> References
              </h2>
              <ol className="references-list">
                {report.references.map((ref, i) => (
                  <li key={i} className="reference-item">{ref}</li>
                ))}
              </ol>
            </section>
          )}
        </div>
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
    <div className="paper-card" id={`paper-${paper.id}`}>
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

        <div className={`paper-summary-content ${isExpanded ? 'expanded' : ''}`}>
          <ReactMarkdown>{displaySummary}</ReactMarkdown>
        </div>

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
    </div>
  );
}

function generateMarkdown(report) {
  let md = `# Research Report: ${report.topic}\n\n`;
  md += `*Generated: ${new Date(report.generated_at).toLocaleString()}*\n\n`;
  md += `## Summary\n\n${report.summary}\n\n`;

  if (report.key_techniques?.length) {
    md += `## Key Techniques\n\n`;
    report.key_techniques.forEach((t) => (md += `- ${t}\n`));
    md += '\n';
  }

  if (report.comparison_table?.length) {
    md += `## Comparison Table\n\n`;
    md += `| Method | Description | Strengths | Limitations |\n`;
    md += `|--------|-------------|-----------|-------------|\n`;
    report.comparison_table.forEach((r) => {
      md += `| ${r.method} | ${r.description} | ${r.strengths} | ${r.limitations} |\n`;
    });
    md += '\n';
  }

  if (report.future_directions?.length) {
    md += `## Future Directions\n\n`;
    report.future_directions.forEach((d, i) => (md += `${i + 1}. ${d}\n`));
    md += '\n';
  }

  if (report.references?.length) {
    md += `## References\n\n`;
    report.references.forEach((r, i) => (md += `${i + 1}. ${r}\n`));
  }

  return md;
}
