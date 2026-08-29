import React from 'react';

interface BadgeProps {
  label: string;
  color?: 'primary' | 'secondary' | 'tertiary' | 'error';
}

const Badge: React.FC<BadgeProps> = ({ label, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary text-on-primary',
    secondary: 'bg-secondary text-on-secondary',
    tertiary: 'bg-tertiary text-on-tertiary',
    error: 'bg-error text-on-error',
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-md ${colorClasses[color]}`}>
      {label}
    </span>
  );
};

export default Badge;