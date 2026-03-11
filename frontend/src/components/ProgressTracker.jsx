import { HiOutlineMagnifyingGlass } from 'react-icons/hi2';
import './ProgressTracker.css';

const STAGES = [
  { key: 'searching', label: 'Searching', icon: '🔍' },
  { key: 'reading', label: 'Reading Papers', icon: '📄' },
  { key: 'indexing', label: 'Building RAG Index', icon: '🧠' },
  { key: 'summarizing', label: 'Summarizing', icon: '📝' },
  { key: 'evaluating', label: 'Evaluating', icon: '⚖️' },
  { key: 'writing', label: 'Writing Report', icon: '✍️' },
  { key: 'completed', label: 'Complete!', icon: '✅' },
];

const STAGE_ORDER = STAGES.map((s) => s.key);

export default function ProgressTracker({ currentStage, progress, status }) {
  const currentIndex = STAGE_ORDER.indexOf(currentStage);
  const isFailed = status === 'failed';

  return (
    <div className="progress-tracker" id="progress-tracker">
      {/* Progress bar */}
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
        <span className="progress-bar-label">{progress}%</span>
      </div>

      {/* Stage steps */}
      <div className="stages-container">
        {STAGES.map((stage, index) => {
          let stageClass = 'stage-pending';
          if (isFailed) {
            stageClass = index <= currentIndex ? 'stage-failed' : 'stage-pending';
          } else if (index < currentIndex) {
            stageClass = 'stage-completed';
          } else if (index === currentIndex) {
            stageClass = stage.key === 'completed' ? 'stage-completed' : 'stage-active';
          }

          return (
            <div className={`stage ${stageClass}`} key={stage.key}>
              <div className="stage-dot">
                <span className="stage-icon">{stage.icon}</span>
              </div>
              <span className="stage-label">{stage.label}</span>
              {index < STAGES.length - 1 && (
                <div className={`stage-connector ${index < currentIndex ? 'filled' : ''}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
