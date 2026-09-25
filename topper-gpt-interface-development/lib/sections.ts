import {
  Bot,
  FileSpreadsheet,
  NotebookPen,
  Compass,
  Users,
  type LucideIcon,
} from 'lucide-react'

export type SectionId =
  | 'tutor'
  | 'papers'
  | 'notes'
  | 'research'
  | 'community'

export type Section = {
  id: SectionId
  label: string
  short: string
  description: string
  icon: LucideIcon
  accent: 'cyber' | 'cyan-neon' | 'academic'
}

export const SECTIONS: Section[] = [
  {
    id: 'tutor',
    label: 'AI Tutor',
    short: 'Ask anything, learn faster',
    description:
      'Conversational tutor with code, math, and document context awareness.',
    icon: Bot,
    accent: 'cyber',
  },
  {
    id: 'papers',
    label: 'Predicted Question Papers',
    short: 'Mumbai University predictor',
    description:
      'Forecast likely exam questions with frequency analytics and accuracy metrics.',
    icon: FileSpreadsheet,
    accent: 'academic',
  },
  {
    id: 'notes',
    label: 'Smart Notes Synthesizer',
    short: 'PDF to structured summary',
    description:
      'Turn dense PDFs into structured, exam-ready summaries in seconds.',
    icon: NotebookPen,
    accent: 'cyan-neon',
  },
  {
    id: 'research',
    label: 'Topic Research Hub',
    short: 'Deep-dive any concept',
    description:
      'Curated learning paths, references, and concept maps for any topic.',
    icon: Compass,
    accent: 'cyber',
  },
  {
    id: 'community',
    label: 'Community Insights',
    short: 'Learn with 40k+ toppers',
    description:
      'Trending doubts, shared notes, and crowd-sourced exam intelligence.',
    icon: Users,
    accent: 'cyan-neon',
  },
]

export const ACCENT_HEX: Record<Section['accent'], string> = {
  cyber: '#3b82f6',
  'cyan-neon': '#06b6d4',
  academic: '#ea580c',
}
