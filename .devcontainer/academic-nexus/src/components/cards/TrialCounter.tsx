import React from 'react';

interface TrialCounterProps {
  currentQueries: number;
  totalQueries: number;
}

const TrialCounter: React.FC<TrialCounterProps> = ({ currentQueries, totalQueries }) => {
  const progressPercentage = (currentQueries / totalQueries) * 100;

  return (
    <div className="trial-counter bg-[#0B0F19] border border-[#2A3241] rounded-md p-4">
      <h3 className="text-[#00F2FE] font-semibold text-lg">Trial Counter</h3>
      <div className="flex items-center justify-between mt-2">
        <span className="text-[#dee2f2]">
          {currentQueries}/{totalQueries} Queries Used
        </span>
        <span className="text-[#10B981] font-bold">{progressPercentage.toFixed(0)}%</span>
      </div>
      <div className="bg-[#161B26] rounded-md mt-2">
        <div
          className="bg-[#00F2FE] rounded-md h-2"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
    </div>
  );
};

export default TrialCounter;