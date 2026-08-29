import React from 'react';

interface FormulaBoxProps {
  formula: string;
  highlight?: boolean;
}

const FormulaBox: React.FC<FormulaBoxProps> = ({ formula, highlight }) => {
  return (
    <div
      className={`bg-[#0B0F19] border-dashed border-[#00F2FE] rounded-md p-4 ${
        highlight ? 'bg-opacity-10' : ''
      }`}
    >
      <span className="text-[#00F2FE] text-lg font-medium">{formula}</span>
    </div>
  );
};

export default FormulaBox;