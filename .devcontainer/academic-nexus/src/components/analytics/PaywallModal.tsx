import React from 'react';
import { useState } from 'react';
import { Button } from '../ui/Button';
import './PaywallModal.css'; // Assuming you have a CSS file for styles

const PaywallModal = ({ isOpen, onClose }) => {
    const [isAnnual, setIsAnnual] = useState(false);

    const handleToggle = () => {
        setIsAnnual(!isAnnual);
    };

    const handleUnlock = () => {
        // Logic to handle unlocking premium features
        console.log('Unlocking premium features...');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="paywall-modal">
            <div className="paywall-modal-content">
                <h2 className="paywall-title">Unlock Topper Pro</h2>
                <p className="paywall-description">
                    Get access to premium features and analytics to enhance your learning experience.
                </p>
                <div className="pricing-toggle">
                    <span className={`toggle-option ${!isAnnual ? 'active' : ''}`} onClick={handleToggle}>
                        Semester
                    </span>
                    <span className={`toggle-option ${isAnnual ? 'active' : ''}`} onClick={handleToggle}>
                        Annual
                    </span>
                </div>
                <div className="pricing-details">
                    <p className="price">
                        {isAnnual ? '$99.99/year' : '$19.99/semester'}
                    </p>
                </div>
                <Button onClick={handleUnlock} className="unlock-button">
                    Unlock Now
                </Button>
                <Button onClick={onClose} className="close-button">
                    Close
                </Button>
            </div>
        </div>
    );
};

export default PaywallModal;