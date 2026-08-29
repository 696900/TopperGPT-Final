import React from 'react';
import './LockedAnalytics.css'; // Assuming you have a CSS file for styling

const LockedAnalytics: React.FC = () => {
    return (
        <div className="locked-analytics-container">
            <div className="blurred-background">
                <h2 className="locked-title">Unlock Topper Pro</h2>
                <p className="locked-description">
                    This feature is locked. Upgrade to Topper Pro to access advanced analytics and insights.
                </p>
                <button className="unlock-button">Unlock Now</button>
            </div>
        </div>
    );
};

export default LockedAnalytics;