export type PredictedQuestion = {
  q: string
  marks: number
  probability: number // 0-100
  appeared: number[] // years it appeared
  unit: string
  type: 'Derivation' | 'Numerical' | 'Theory' | 'Diagram' | 'Short note'
}

export type PaperSubject = {
  id: string
  name: string
  code: string
  semester: number
  branch: string
  accuracy: number // historical predictor accuracy %
  questions: PredictedQuestion[]
}

export const SUBJECTS: PaperSubject[] = [
  {
    id: 'dsa',
    name: 'Data Structures & Analysis',
    code: 'CSC303',
    semester: 3,
    branch: 'Computer Engineering',
    accuracy: 91,
    questions: [
      {
        q: 'Explain AVL tree rotations with an example of insertion causing LL and LR imbalance.',
        marks: 10,
        probability: 88,
        appeared: [2021, 2022, 2024],
        unit: 'Unit III',
        type: 'Theory',
      },
      {
        q: "Write an algorithm for Dijkstra's shortest path and trace it on a given graph.",
        marks: 10,
        probability: 82,
        appeared: [2020, 2023, 2024],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Compare linear and non-linear data structures with suitable examples.',
        marks: 5,
        probability: 74,
        appeared: [2019, 2022],
        unit: 'Unit I',
        type: 'Theory',
      },
      {
        q: 'Convert the given infix expression to postfix using a stack.',
        marks: 8,
        probability: 69,
        appeared: [2021, 2023],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Short note on hashing and collision resolution techniques.',
        marks: 5,
        probability: 61,
        appeared: [2020, 2024],
        unit: 'Unit VI',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'os',
    name: 'Operating Systems',
    code: 'CSC404',
    semester: 4,
    branch: 'Computer Engineering',
    accuracy: 87,
    questions: [
      {
        q: 'Explain the Banker’s algorithm for deadlock avoidance with an example.',
        marks: 10,
        probability: 90,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit IV',
        type: 'Numerical',
      },
      {
        q: 'Compare paging and segmentation memory management schemes.',
        marks: 8,
        probability: 78,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Theory',
      },
      {
        q: 'Solve the given process set using SJF and Round Robin; compute average waiting time.',
        marks: 10,
        probability: 84,
        appeared: [2019, 2022, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Explain the producer-consumer problem and its solution using semaphores.',
        marks: 8,
        probability: 71,
        appeared: [2020, 2023],
        unit: 'Unit III',
        type: 'Theory',
      },
      {
        q: 'Short note on virtual memory and page replacement policies.',
        marks: 5,
        probability: 66,
        appeared: [2021, 2024],
        unit: 'Unit V',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'em',
    name: 'Engineering Mathematics III',
    code: 'FEC301',
    semester: 3,
    branch: 'Common (All Branches)',
    accuracy: 84,
    questions: [
      {
        q: 'Find the Laplace transform of a given piecewise function and its inverse.',
        marks: 10,
        probability: 86,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit I',
        type: 'Numerical',
      },
      {
        q: 'Obtain the Fourier series expansion of f(x) in the interval (-π, π).',
        marks: 10,
        probability: 80,
        appeared: [2019, 2022, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Verify Green’s theorem for the given vector field over a region.',
        marks: 8,
        probability: 72,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Derivation',
      },
      {
        q: 'Solve the given differential equation using the method of variation of parameters.',
        marks: 8,
        probability: 68,
        appeared: [2020, 2022],
        unit: 'Unit II',
        type: 'Numerical',
      },
    ],
  },
]

export const PREDICTION_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
