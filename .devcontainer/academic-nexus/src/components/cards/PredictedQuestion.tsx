import React from 'react';

interface PredictedQuestionProps {
  question: string;
  probability: number;
}

const PredictedQuestion: React.FC<PredictedQuestionProps> = ({ question, probability }) => {
  return (
    <div className="predicted-question-card">
      <h3 className="predicted-question">{question}</h3>
      <div className="probability-score">
        <span>{probability}% Likely</span>
      </div>
      <style jsx>{`
        .predicted-question-card {
          background-color: #0b0f19;
          border: 1px dashed #00f2fe;
          border-radius: 0.25rem;
          padding: 16px;
          margin: 16px 0;
          transition: transform 0.2s ease;
        }
        .predicted-question-card:hover {
          transform: scale(1.02);
        }
        .predicted-question {
          font-family: 'Inter', sans-serif;
          font-size: 20px;
          font-weight: 600;
          color: #dee2f2;
        }
        .probability-score {
          margin-top: 8px;
          font-family: 'Inter', sans-serif;
          font-size: 14px;
          font-weight: 400;
          color: #4edea3;
        }
      `}</style>
    </div>
  );
};

export default PredictedQuestion;