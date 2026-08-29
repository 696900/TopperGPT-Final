import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatMessage } from '../../types/chat';

interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    sendMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload);
    },
    receiveMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload);
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    clearChat(state) {
      state.messages = [];
    },
  },
});

export const { sendMessage, receiveMessage, setLoading, setError, clearChat } = chatSlice.actions;

export default chatSlice.reducer;