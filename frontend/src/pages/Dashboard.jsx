import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HiOutlineRocketLaunch,
  HiOutlineDocumentText,
  HiOutlineCpuChip,
  HiOutlineGlobeAlt,
  HiOutlineAcademicCap,
  HiOutlineArrowRight,
} from 'react-icons/hi2';
import { submitResearch } from '../services/api';
import './Dashboard.css';

const FEATURES = [
  {
    icon: HiOutlineGlobeAlt,
    title: 'Web Search',
    desc: 'Searches the internet and Arxiv for the latest papers.',
    color: 'var(--accent-cyan)',
  },
  {
    icon: HiOutlineDocumentText,
    title: 'Paper Analysis',
    desc: 'Downloads PDFs and extracts key information.',
    color: 'var(--accent-purple)',
  },
  {
    icon: HiOutlineCpuChip,
    title: 'AI Summarization',
    desc: 'LLM-powered summaries with hallucination checking.',
    color: 'var(--accent-blue)',
  },
  {
    icon: HiOutlineAcademicCap,
    title: 'Structured Reports',
    desc: 'Generates comparison tables, insights, and citations.',
    color: 'var(--accent-amber)',
  },
];

const EXAMPLE_TOPICS = [
  'Latest methods for improving LLM reasoning',
  'Advancements in multimodal AI systems',
  'State-of-the-art techniques in AI safety and alignment',
  'Recent breakthroughs in protein structure prediction',
];

export default function Dashboard() {
  const [topic, setTopic] = useState('');
  const [maxPapers, setMaxPapers] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsSubmitting(true);
    setError('');

    try {
      const result = await submitResearch(topic.trim(), maxPapers);
      navigate(`/research/${result.task_id}`);
    } catch (err) {
      setError(err.message || 'Failed to submit research task.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExampleClick = (example) => {
    setTopic(example);
  };

  return (
    <div className="dashboard" id="dashboard-page">
      {/* Hero Section */}
      <section className="hero animate-fade-in-up">
        <div className="hero-badge">
          <HiOutlineRocketLaunch />
          <span>Autonomous AI Research Agent</span>
        </div>
        <h1 className="hero-title">
          Research Any Topic with{' '}
          <span className="gradient-text">AI Agents</span>
        </h1>
        <p className="hero-description">
          Submit a research question and let multiple AI agents search the web,
          read papers, summarize findings, and generate a comprehensive
          structured report — automatically.
        </p>
      </section>

      {/* Research Form */}
      <section className="research-form-section animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <form onSubmit={handleSubmit} className="research-form glass-card" id="research-form">
          <div className="form-group">
            <label htmlFor="research-topic" className="form-label">
              Research Topic
            </label>
            <textarea
              id="research-topic"
              className="form-input"
              rows="3"
              placeholder="e.g., Latest methods for improving LLM reasoning..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              maxLength={500}
              required
            />
            <span className="char-count">{topic.length}/500</span>
          </div>

          <div className="form-row">
            <div className="form-group form-group-sm">
              <label htmlFor="max-papers" className="form-label">
                Max Papers
              </label>
              <input
                id="max-papers"
                type="number"
                className="form-input"
                min={1}
                max={20}
                value={maxPapers}
                onChange={(e) => setMaxPapers(Number(e.target.value))}
              />
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={isSubmitting || !topic.trim()}
              id="submit-research-btn"
            >
              {isSubmitting ? (
                <>
                  <span className="btn-spinner" />
                  Processing...
                </>
              ) : (
                <>
                  Start Research
                  <HiOutlineArrowRight />
                </>
              )}
            </button>
          </div>

          {error && <div className="form-error">{error}</div>}
        </form>
      </section>

      {/* Example Topics */}
      <section className="examples-section animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
        <h3 className="section-title">Try an example</h3>
        <div className="examples-grid">
          {EXAMPLE_TOPICS.map((example, i) => (
            <button
              key={i}
              className="example-chip"
              onClick={() => handleExampleClick(example)}
              id={`example-topic-${i}`}
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="features-section animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
        <h3 className="section-title">How it works</h3>
        <div className="features-grid">
          {FEATURES.map((feat, i) => {
            const Icon = feat.icon;
            return (
              <div className="feature-card glass-card" key={i} style={{ animationDelay: `${0.3 + i * 0.1}s` }}>
                <div className="feature-icon" style={{ color: feat.color, background: `${feat.color}15` }}>
                  <Icon />
                </div>
                <h4 className="feature-title">{feat.title}</h4>
                <p className="feature-desc">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
