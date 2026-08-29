import React from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useChat } from '../../features/chat';

export const ChatThread: React.FC = () => {
    const { messages } = useChat();

    return (
        <div className="chat-thread" style={{ padding: '24px', backgroundColor: '#0e131e', borderRadius: '0.25rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div className="messages" style={{ flex: 1, overflowY: 'auto' }}>
                {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                ))}
            </div>
            <ChatInput />
        </div>
    );
};