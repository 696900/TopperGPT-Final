import React from 'react';

interface CardProps {
  title: string;
  content: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ title, content, footer, className }) => {
  return (
    <div className={`bg-surface-container rounded-lg p-4 shadow-md ${className}`}>
      <h2 className="text-display-lg font-semibold text-on-surface">{title}</h2>
      <div className="mt-2 text-body-md text-on-surface-variant">
        {content}
      </div>
      {footer && <div className="mt-4 border-t border-outline pt-2">{footer}</div>}
    </div>
  );
};

export default Card;