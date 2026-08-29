export interface StudyTopic {
  id: string;
  title: string;
  description: string;
  resources: string[];
  progress: number; // Percentage of completion
}

export interface StudySession {
  id: string;
  topicId: string;
  startTime: Date;
  endTime: Date;
  duration: number; // Duration in minutes
  notes: string;
}

export interface StudyAnalytics {
  totalSessions: number;
  totalStudyTime: number; // Total time spent studying in minutes
  topicsCompleted: number;
  progressByTopic: Record<string, number>; // Topic ID to progress percentage
}