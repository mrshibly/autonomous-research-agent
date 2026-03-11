import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HiOutlineClock,
  HiOutlineTrash,
  HiOutlineDocumentMagnifyingGlass,
  HiOutlineFolderOpen,
} from 'react-icons/hi2';
import { getResearchHistory, deleteResearch } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import './History.css';

export default function History() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const result = await getResearchHistory(page, 20);
      setData(result);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page]);

  const handleDelete = async (taskId, e) => {
    e.stopPropagation();
    if (!confirm('Delete this research task?')) return;
    try {
      await deleteResearch(taskId);
      fetchHistory();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const filteredTasks = data?.tasks?.filter((t) =>
    t.topic.toLowerCase().includes(search.toLowerCase())
  ) || [];

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <div className="history-page" id="history-page">
      <div className="history-header animate-fade-in-up">
        <div>
          <h1 className="history-title">Research History</h1>
          <p className="history-subtitle">
            {data?.total || 0} total research tasks
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="history-search animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <HiOutlineDocumentMagnifyingGlass className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Filter by topic..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          id="history-search-input"
        />
      </div>

      {/* Content */}
      {loading && !data ? (
        <LoadingSpinner size="lg" message="Loading history..." />
      ) : filteredTasks.length === 0 ? (
        <div className="empty-state animate-fade-in">
          <HiOutlineFolderOpen className="empty-icon" />
          <h3>No research tasks yet</h3>
          <p>Submit a research topic from the dashboard to get started.</p>
        </div>
      ) : (
        <>
          <div className="history-list">
            {filteredTasks.map((task, i) => (
              <div
                key={task.task_id}
                className="history-card glass-card animate-fade-in-up"
                style={{ animationDelay: `${0.1 + i * 0.05}s` }}
                onClick={() => navigate(`/research/${task.task_id}`)}
                id={`history-card-${task.task_id}`}
              >
                <div className="history-card-content">
                  <h3 className="history-topic">{task.topic}</h3>
                  <div className="history-meta">
                    <span className={`status-badge status-${task.status}`}>
                      {task.status}
                    </span>
                    <span className="meta-item">
                      <HiOutlineClock />
                      {new Date(task.created_at).toLocaleDateString()}
                    </span>
                    <span className="meta-item">
                      {task.papers_count} papers
                    </span>
                    {task.status !== 'completed' && task.status !== 'failed' && (
                      <span className="meta-item">
                        {task.progress}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="history-progress-bar">
                  <div
                    className="history-progress-fill"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>

                <button
                  className="delete-btn"
                  onClick={(e) => handleDelete(task.task_id, e)}
                  title="Delete task"
                  id={`delete-task-${task.task_id}`}
                >
                  <HiOutlineTrash />
                </button>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="page-btn"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </button>
              <span className="page-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="page-btn"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
