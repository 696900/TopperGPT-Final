import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { StudyState, StudyData } from '../../types/study';

const initialState: StudyState = {
  topics: [],
  progress: 0,
  trialUsage: 0,
};

const studySlice = createSlice({
  name: 'study',
  initialState,
  reducers: {
    setTopics(state, action: PayloadAction<StudyData[]>) {
      state.topics = action.payload;
    },
    updateProgress(state, action: PayloadAction<number>) {
      state.progress = action.payload;
    },
    incrementTrialUsage(state) {
      state.trialUsage += 1;
    },
    resetTrialUsage(state) {
      state.trialUsage = 0;
    },
  },
});

export const { setTopics, updateProgress, incrementTrialUsage, resetTrialUsage } = studySlice.actions;

export default studySlice.reducer;