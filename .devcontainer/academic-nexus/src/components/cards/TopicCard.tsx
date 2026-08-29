import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface TopicCardProps {
  title: string;
  description: string;
  progress: number; // Progress as a percentage
  onClick: () => void;
}

const TopicCard: React.FC<TopicCardProps> = ({ title, description, progress, onClick }) => {
  return (
    <Card onClick={onClick} className="flex flex-col p-4 bg-surface-container rounded-lg hover:shadow-lg transition-shadow duration-200">
      <h3 className="text-display-lg text-on-surface">{title}</h3>
      <p className="text-body-md text-on-surface-variant mt-2">{description}</p>
      <div className="mt-4">
        <Badge text={`${progress}% Complete`} />
      </div>
    </Card>
  );
};

export default TopicCard;