export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

export interface ChatThread {
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
}

export interface ChatInputProps {
  onSend: (message: string) => void;
}

export interface FormulaBoxProps {
  formula: string;
  description?: string;
}