import React from 'react';
import { Link } from 'react-router-dom';
import { useTrialCounter } from '../../hooks/useTrialCounter';
import { ReactComponent as AcademicNexusIcon } from '../../assets/icon.svg'; // Assuming you have an icon for the sidebar

const Sidebar: React.FC = () => {
  const { trialCount, maxTrials } = useTrialCounter();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <AcademicNexusIcon className="sidebar-icon" />
        <h1 className="sidebar-title">Academic Nexus</h1>
      </div>
      <nav className="sidebar-nav">
        <ul>
          <li>
            <Link to="/dashboard">Dashboard</Link>
          </li>
          <li>
            <Link to="/study">Study</Link>
          </li>
          <li>
            <Link to="/chat">Chat</Link>
          </li>
          <li>
            <Link to="/analytics">Analytics</Link>
          </li>
          <li>
            <Link to="/billing">Billing</Link>
          </li>
        </ul>
      </nav>
      <div className="trial-counter">
        <p>{trialCount}/{maxTrials} Free Queries</p>
      </div>
    </aside>
  );
};

export default Sidebar;