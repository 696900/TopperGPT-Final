export type GuardrailStatus = 'academic' | 'borderline' | 'offtopic' | 'idle'

export type GuardrailResult = {
  status: GuardrailStatus
  label: string
  hint: string
}

const ACADEMIC_SIGNALS = [
  'engineering',
  'equation',
  'theorem',
  'circuit',
  'algorithm',
  'derivative',
  'integral',
  'thermodynamics',
  'semiconductor',
  'compiler',
  'data structure',
  'operating system',
  'network',
  'physics',
  'chemistry',
  'calculus',
  'matrix',
  'voltage',
  'exam',
  'syllabus',
  'formula',
  'proof',
  'complexity',
  'kinematics',
  'signal',
  'microprocessor',
  'database',
  'java',
  'python',
  'c++',
  'math',
  'solve',
  'derive',
  'explain',
  'define',
  'theory',
  'concept',
  'problem',
  'question',
  'unit',
  'module',
  'assignment',
]

const OFFTOPIC_SIGNALS = [
  'dating',
  'gossip',
  'stock tip',
  'gambling',
  'crypto pump',
  'celebrity',
  'politics',
  'roast',
  'joke about',
  'movie recommendation',
  'weather',
  'horoscope',
  'relationship advice',
]

export function analyzeQuery(input: string): GuardrailResult {
  const text = input.trim().toLowerCase()
  if (!text) {
    return {
      status: 'idle',
      label: 'Ready',
      hint: 'Ask an academic or engineering question.',
    }
  }

  const offtopic = OFFTOPIC_SIGNALS.some((s) => text.includes(s))
  if (offtopic) {
    return {
      status: 'offtopic',
      label: 'Off-syllabus',
      hint: 'TopperGPT stays focused on academics & engineering — try rephrasing toward your coursework.',
    }
  }

  const matches = ACADEMIC_SIGNALS.filter((s) => text.includes(s)).length
  if (matches >= 1 || text.length > 40) {
    return {
      status: 'academic',
      label: 'On-topic',
      hint: 'Great — this looks academic. TopperGPT will give a rigorous answer.',
    }
  }

  return {
    status: 'borderline',
    label: 'Add detail',
    hint: 'Add a subject or concept so the tutor can stay academically precise.',
  }
}
