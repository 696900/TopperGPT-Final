import React, { useState } from 'react';
import { useChat } from '../../features/chat';
import './ChatInput.css';

const ChatInput: React.FC = () => {
    const [inputValue, setInputValue] = useState('');
    const { sendMessage } = useChat();

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(event.target.value);
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (inputValue.trim()) {
            sendMessage(inputValue);
            setInputValue('');
        }
    };

    return (
        <form className="chat-input" onSubmit={handleSubmit}>
            <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                placeholder="Type your message..."
                className="chat-input-field"
                autoComplete="off"
            />
            <button type="submit" className="chat-input-button">
                Send
            </button>
        </form>
    );
};

export default ChatInput;