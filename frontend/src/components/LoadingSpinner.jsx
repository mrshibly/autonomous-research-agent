import './LoadingSpinner.css';

export default function LoadingSpinner({ size = 'md', message = '' }) {
  return (
    <div className={`spinner-container spinner-${size}`} id="loading-spinner">
      <div className="spinner">
        <div className="spinner-ring" />
        <div className="spinner-ring" />
        <div className="spinner-ring" />
        <div className="spinner-core" />
      </div>
      {message && <p className="spinner-message">{message}</p>}
    </div>
  );
}
