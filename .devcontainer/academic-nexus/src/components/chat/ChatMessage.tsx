import React from 'react';
import { ChatMessageType } from '../../types/chat';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUserMessage = message.sender === 'user';

  return (
    <div
      className={`flex ${
        isUserMessage ? 'justify-end' : 'justify-start'
      } mb-4`}
    >
      <div
        className={`max-w-xs p-3 rounded-lg ${
          isUserMessage ? 'bg-surface-container-high' : 'bg-surface-container'
        } border ${
          isUserMessage ? 'border-transparent' : 'border-outline'
        }`}
      >
        <p className={`text-body-md text-on-surface`}>
          {message.text}
        </p>
      </div>
    </div>
  );
};

export default ChatMessage;