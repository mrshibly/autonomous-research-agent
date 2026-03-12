import { NavLink, useLocation } from 'react-router-dom';
import {
  HiOutlineHome,
  HiOutlineClock,
  HiOutlineBeaker,
  HiOutlineSparkles,
} from 'react-icons/hi2';
import './Sidebar.css';

const navItems = [
  { path: '/', icon: HiOutlineHome, label: 'Dashboard' },
  { path: '/history', icon: HiOutlineClock, label: 'History' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="sidebar" id="sidebar-nav">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon">
            <HiOutlineBeaker />
          </div>
          <div className="logo-text">
            <span className="logo-title gradient-text">AI Research</span>
            <span className="logo-subtitle">Autonomous Agent</span>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              to={item.path}
              key={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
              id={`nav-${item.label.toLowerCase()}`}
            >
              <Icon className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {isActive && <div className="nav-indicator" />}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="social-links">
          <a href="https://github.com/mrshibly" target="_blank" rel="noopener noreferrer" className="social-link" title="GitHub">
            <HiOutlineSparkles className="badge-icon" />
            <span>@mrshibly</span>
          </a>
          <div className="social-divider" />
          <a href="https://linkedin.com/in/mrshibly" target="_blank" rel="noopener noreferrer" className="social-link" title="LinkedIn">
             <HiOutlineLink className="badge-icon" />
             <span>LinkedIn</span>
          </a>
        </div>
      </div>
    </aside>
  );
}
