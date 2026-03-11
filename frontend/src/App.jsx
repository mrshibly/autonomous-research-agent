import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ResearchView from './pages/ResearchView';
import History from './pages/History';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout" id="app-root">
        <Sidebar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/research/:taskId" element={<ResearchView />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
