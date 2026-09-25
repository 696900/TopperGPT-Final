export type PredictedQuestion = {
  q: string
  marks: number
  probability: number // 0-100
  appeared: number[] // years it appeared in Mumbai University papers
  unit: string
  type: 'Derivation' | 'Numerical' | 'Theory' | 'Diagram' | 'Short note'
  frequencyBadge?: string // e.g. "Repeated 5x (2019-2024)"
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
    accuracy: 93,
    questions: [
      {
        q: 'Explain AVL tree rotations with a step-by-step example of insertion causing LL and LR imbalance.',
        marks: 10,
        probability: 95,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Theory',
      },
      {
        q: "Write an algorithm for Dijkstra's shortest path and trace it on a given directed weighted graph.",
        marks: 10,
        probability: 91,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Construct a B-tree of order 5 by inserting given keys. Explain the node splitting mechanism.',
        marks: 10,
        probability: 88,
        appeared: [2019, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Convert the given infix expression to postfix using a stack with tabular trace.',
        marks: 8,
        probability: 84,
        appeared: [2020, 2022, 2024],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Compare linear and non-linear data structures with real-world application examples.',
        marks: 5,
        probability: 76,
        appeared: [2021, 2023],
        unit: 'Unit I',
        type: 'Theory',
      },
      {
        q: 'Explain collision resolution techniques in Hashing: Linear probing vs Chaining.',
        marks: 8,
        probability: 74,
        appeared: [2022, 2024],
        unit: 'Unit VI',
        type: 'Theory',
      },
      {
        q: 'Short note on Double Ended Queue (Deque) and its array implementation.',
        marks: 5,
        probability: 65,
        appeared: [2023],
        unit: 'Unit II',
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
    accuracy: 92,
    questions: [
      {
        q: "Explain Banker's algorithm for deadlock avoidance. Given Allocation, Max, and Available matrices, determine if the system is in a safe state.",
        marks: 10,
        probability: 96,
        appeared: [2019, 2020, 2022, 2023, 2024],
        unit: 'Unit IV',
        type: 'Numerical',
      },
      {
        q: 'Solve the process scheduling problem using Preemptive SJF (SRTF) and Round Robin (Quantum=2ms). Compute average turnaround and waiting times.',
        marks: 10,
        probability: 93,
        appeared: [2020, 2021, 2022, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Explain Paging vs Segmentation. How does TLB accelerate address translation? Draw the architecture diagram.',
        marks: 10,
        probability: 89,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit V',
        type: 'Diagram',
      },
      {
        q: 'Explain Producer-Consumer problem and Readers-Writers problem using counting semaphores.',
        marks: 8,
        probability: 83,
        appeared: [2021, 2023, 2024],
        unit: 'Unit III',
        type: 'Theory',
      },
      {
        q: 'Compare FIFO, LRU, and Optimal page replacement algorithms for a given reference string.',
        marks: 10,
        probability: 81,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Explain disk scheduling algorithms: SCAN, C-SCAN, and SSTF with head movement calculation.',
        marks: 8,
        probability: 72,
        appeared: [2022, 2024],
        unit: 'Unit VI',
        type: 'Numerical',
      },
      {
        q: 'Short note on Critical Section Problem and Peterson’s solution.',
        marks: 5,
        probability: 68,
        appeared: [2023],
        unit: 'Unit III',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'em3',
    name: 'Engineering Mathematics III',
    code: 'FEC301',
    semester: 3,
    branch: 'Common (All Branches)',
    accuracy: 89,
    questions: [
      {
        q: 'Find the Laplace transform of periodic functions and evaluate the inverse Laplace using convolution theorem.',
        marks: 10,
        probability: 94,
        appeared: [2019, 2020, 2021, 2023, 2024],
        unit: 'Unit I',
        type: 'Numerical',
      },
      {
        q: 'Obtain the Fourier series expansion of f(x) = x^2 in the interval (-π, π) and deduce that π^2/12 = 1 - 1/4 + 1/9 - 1/16...',
        marks: 10,
        probability: 91,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Derivation',
      },
      {
        q: 'Verify Green’s theorem in the plane for ∮ (xy + y^2)dx + x^2 dy where C is the boundary of the region enclosed by y = x and y = x^2.',
        marks: 8,
        probability: 86,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Find the analytic function f(z) = u + iv if u = e^x (x cos y - y sin y) using Milne-Thomson method.',
        marks: 8,
        probability: 82,
        appeared: [2021, 2023, 2024],
        unit: 'Unit IV',
        type: 'Numerical',
      },
      {
        q: 'Solve the second-order ordinary differential equation using Method of Variation of Parameters.',
        marks: 8,
        probability: 77,
        appeared: [2020, 2022],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Short note on Bilinear Transformation and Cross Ratio property.',
        marks: 5,
        probability: 69,
        appeared: [2022, 2024],
        unit: 'Unit IV',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'dbms',
    name: 'Database Management Systems',
    code: 'CSC403',
    semester: 4,
    branch: 'Computer Engineering',
    accuracy: 91,
    questions: [
      {
        q: 'Design an ER diagram for a Hospital Management System and convert it into relational schemas with primary and foreign keys.',
        marks: 10,
        probability: 95,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit I',
        type: 'Diagram',
      },
      {
        q: 'Explain normalization with functional dependencies: Define 1NF, 2NF, 3NF, and BCNF with decomposing examples.',
        marks: 10,
        probability: 93,
        appeared: [2020, 2021, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Theory',
      },
      {
        q: 'Explain ACID properties of transactions and Two-Phase Locking (2PL) protocol with Strict 2PL vs Rigorous 2PL.',
        marks: 10,
        probability: 88,
        appeared: [2020, 2022, 2024],
        unit: 'Unit V',
        type: 'Theory',
      },
      {
        q: 'Write complex SQL queries involving nested subqueries, GROUP BY, HAVING, and correlated subqueries on Employee database.',
        marks: 10,
        probability: 85,
        appeared: [2019, 2022, 2023],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Explain conflict serializability with precedence graph method. Check whether given schedule S is conflict serializable.',
        marks: 8,
        probability: 79,
        appeared: [2021, 2024],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Short note on indexing techniques: B+ Tree index vs Hash index.',
        marks: 5,
        probability: 70,
        appeared: [2023, 2024],
        unit: 'Unit IV',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'cn',
    name: 'Computer Networks',
    code: 'CSC502',
    semester: 5,
    branch: 'Computer Engineering',
    accuracy: 90,
    questions: [
      {
        q: 'Explain IPv4 addressing, Subnetting, and CIDR. Given IP 192.168.10.0/26, determine network ID, broadcast address, and host range.',
        marks: 10,
        probability: 94,
        appeared: [2019, 2020, 2022, 2023, 2024],
        unit: 'Unit IV',
        type: 'Numerical',
      },
      {
        q: 'Explain TCP 3-Way Handshake connection establishment and TCP 4-Way connection termination with state transition diagrams.',
        marks: 10,
        probability: 92,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit V',
        type: 'Diagram',
      },
      {
        q: 'Compare distance vector routing (Bellman-Ford) vs link state routing (Dijkstra). Explain count-to-infinity problem.',
        marks: 10,
        probability: 87,
        appeared: [2019, 2022, 2024],
        unit: 'Unit IV',
        type: 'Theory',
      },
      {
        q: 'Explain sliding window protocols: Stop-and-Wait ARQ vs Go-Back-N vs Selective Repeat with efficiency formula.',
        marks: 8,
        probability: 82,
        appeared: [2021, 2023],
        unit: 'Unit III',
        type: 'Derivation',
      },
      {
        q: 'Short note on DNS resolution mechanism (Iterative vs Recursive queries).',
        marks: 5,
        probability: 71,
        appeared: [2022, 2024],
        unit: 'Unit VI',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'dsgt',
    name: 'Discrete Structures & Graph Theory',
    code: 'CSC302',
    semester: 3,
    branch: 'Computer Engineering',
    accuracy: 88,
    questions: [
      {
        q: 'Define Equivalence Relation and Partial Order Relation (Poset). Draw Hasse diagram for divisibility on set D(36).',
        marks: 10,
        probability: 94,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit II',
        type: 'Diagram',
      },
      {
        q: 'State and prove Pigeonhole Principle and Extended Pigeonhole Principle with 2 numerical applications.',
        marks: 8,
        probability: 90,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit I',
        type: 'Theory',
      },
      {
        q: 'Solve the homogeneous and non-homogeneous recurrence relation: a_n - 7a_{n-1} + 12a_{n-2} = 0 with given initial conditions.',
        marks: 10,
        probability: 85,
        appeared: [2019, 2022, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Determine whether given graphs are Isomorphic. Find Eulerian and Hamiltonian paths and circuits.',
        marks: 8,
        probability: 78,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Theory',
      },
      {
        q: 'Short note on Group Theory: Semi-group, Monoid, Group, and Abelian Group with examples.',
        marks: 5,
        probability: 73,
        appeared: [2022, 2024],
        unit: 'Unit IV',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'mp',
    name: 'Microprocessors & Microcontrollers',
    code: 'CSC405',
    semester: 4,
    branch: 'Computer Engineering',
    accuracy: 87,
    questions: [
      {
        q: 'Draw and explain the internal architecture of 8086 microprocessor with Bus Interface Unit (BIU) and Execution Unit (EU).',
        marks: 10,
        probability: 96,
        appeared: [2019, 2020, 2021, 2023, 2024],
        unit: 'Unit I',
        type: 'Diagram',
      },
      {
        q: 'Write an 8086 assembly language program (ALP) to sort an array of 10 numbers in ascending order using bubble sort.',
        marks: 10,
        probability: 91,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Explain 8086 interrupt structure and Interrupt Vector Table (IVT). Differentiate Hardware and Software interrupts.',
        marks: 8,
        probability: 84,
        appeared: [2019, 2022, 2024],
        unit: 'Unit IV',
        type: 'Theory',
      },
      {
        q: 'Interface 8255 PPI with 8086 in Mode 0 and Mode 1. Draw memory interfacing diagram.',
        marks: 10,
        probability: 79,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Diagram',
      },
      {
        q: 'Short note on addressing modes of 8086 with suitable examples.',
        marks: 5,
        probability: 75,
        appeared: [2022, 2024],
        unit: 'Unit II',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'em4',
    name: 'Engineering Mathematics IV',
    code: 'FEC401',
    semester: 4,
    branch: 'Common (All Branches)',
    accuracy: 88,
    questions: [
      {
        q: 'Find eigenvalues and eigenvectors of matrix A and verify Cayley-Hamilton theorem. Compute A^4 and A^-1.',
        marks: 10,
        probability: 95,
        appeared: [2019, 2020, 2022, 2023, 2024],
        unit: 'Unit I',
        type: 'Numerical',
      },
      {
        q: 'Fit a Binomial and Normal distribution for given grouped data and test goodness of fit using Chi-square test at 5% significance level.',
        marks: 10,
        probability: 90,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit IV',
        type: 'Numerical',
      },
      {
        q: 'Solve the Linear Programming Problem (LPP) using Simplex Method and Big-M Method.',
        marks: 10,
        probability: 86,
        appeared: [2019, 2022, 2024],
        unit: 'Unit V',
        type: 'Numerical',
      },
      {
        q: 'Find extremal of the functional ∫ (y\'^2 - y^2 + 2xy) dx using Euler-Lagrange differential equation.',
        marks: 8,
        probability: 80,
        appeared: [2021, 2023],
        unit: 'Unit III',
        type: 'Derivation',
      },
      {
        q: 'Short note on probability density function and Central Limit Theorem.',
        marks: 5,
        probability: 71,
        appeared: [2022, 2024],
        unit: 'Unit IV',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'se',
    name: 'Software Engineering & Agile',
    code: 'CSC504',
    semester: 5,
    branch: 'Computer Engineering',
    accuracy: 89,
    questions: [
      {
        q: 'Compare Waterfall model, Spiral model, and Scrum Agile methodology with life cycle phases and risk analysis.',
        marks: 10,
        probability: 94,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit I',
        type: 'Theory',
      },
      {
        q: 'Calculate Function Point (FP) metrics and COCOMO II effort estimation for a specified software project specification.',
        marks: 10,
        probability: 92,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit III',
        type: 'Numerical',
      },
      {
        q: 'Differentiate Black-box testing (Equivalence partitioning & BVA) vs White-box testing (Basis Path & Cyclomatic complexity).',
        marks: 10,
        probability: 88,
        appeared: [2019, 2022, 2024],
        unit: 'Unit V',
        type: 'Theory',
      },
      {
        q: 'Draw Use Case Diagram, Class Diagram, and Sequence Diagram for an Online Examination Portal.',
        marks: 10,
        probability: 83,
        appeared: [2021, 2023],
        unit: 'Unit II',
        type: 'Diagram',
      },
      {
        q: 'Short note on Software Configuration Management (SCM) and Reverse Engineering.',
        marks: 5,
        probability: 70,
        appeared: [2022, 2024],
        unit: 'Unit VI',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'ai',
    name: 'Artificial Intelligence & Soft Computing',
    code: 'CSC602',
    semester: 6,
    branch: 'Computer / AI-DS',
    accuracy: 90,
    questions: [
      {
        q: 'Explain A* Search algorithm with admissibility and consistency heuristics. Trace A* on 8-puzzle problem.',
        marks: 10,
        probability: 95,
        appeared: [2019, 2020, 2022, 2023, 2024],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Explain Minimax search with Alpha-Beta pruning on a given game tree. Compute pruned branches.',
        marks: 10,
        probability: 91,
        appeared: [2020, 2021, 2023, 2024],
        unit: 'Unit II',
        type: 'Numerical',
      },
      {
        q: 'Convert given English statements to First-Order Predicate Logic (FOPL) and prove using Resolution Refutation.',
        marks: 10,
        probability: 87,
        appeared: [2019, 2022, 2024],
        unit: 'Unit III',
        type: 'Derivation',
      },
      {
        q: 'Explain Backpropagation Learning Algorithm in Multi-Layer Perceptron (MLP) with weight update equations.',
        marks: 10,
        probability: 84,
        appeared: [2021, 2023],
        unit: 'Unit V',
        type: 'Derivation',
      },
      {
        q: 'Short note on Genetic Algorithm operators: Selection, Crossover, and Mutation.',
        marks: 5,
        probability: 72,
        appeared: [2022, 2024],
        unit: 'Unit VI',
        type: 'Short note',
      },
    ],
  },
  {
    id: 'bee',
    name: 'Basic Electrical & Electronics',
    code: 'FEC105',
    semester: 1,
    branch: 'First Year Engineering',
    accuracy: 86,
    questions: [
      {
        q: 'State and prove Thevenin’s and Norton’s theorems. Find current flowing through load resistor RL.',
        marks: 10,
        probability: 96,
        appeared: [2019, 2020, 2021, 2023, 2024],
        unit: 'Unit I',
        type: 'Numerical',
      },
      {
        q: 'Derive EMF equation of a single-phase transformer. Explain open circuit (OC) and short circuit (SC) tests.',
        marks: 10,
        probability: 92,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit IV',
        type: 'Derivation',
      },
      {
        q: 'Explain principle of operation of full wave bridge rectifier with center-tapped transformer, ripple factor, and efficiency.',
        marks: 8,
        probability: 85,
        appeared: [2019, 2022, 2024],
        unit: 'Unit V',
        type: 'Theory',
      },
      {
        q: 'Derive resonant frequency and Q-factor in series RLC AC circuit. Draw resonance curve.',
        marks: 8,
        probability: 80,
        appeared: [2021, 2023],
        unit: 'Unit II',
        type: 'Derivation',
      },
      {
        q: 'Short note on Maximum Power Transfer Theorem with AC circuits.',
        marks: 5,
        probability: 71,
        appeared: [2022, 2024],
        unit: 'Unit I',
        type: 'Short note',
      },
    ],
  },
]

export const PREDICTION_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

/**
 * Filter subjects matching user's search query across name, code, branch, or topics.
 */
export function searchSubjects(query: string): PaperSubject[] {
  const q = query.trim().toLowerCase()
  if (!q) return SUBJECTS
  return SUBJECTS.filter(
    (s) =>
      s.name.toLowerCase().includes(q) ||
      s.code.toLowerCase().includes(q) ||
      s.branch.toLowerCase().includes(q) ||
      s.id.toLowerCase().includes(q) ||
      s.questions.some((item) => item.q.toLowerCase().includes(q) || item.unit.toLowerCase().includes(q)),
  )
}

/**
 * Sorts questions so that high-frequency repeatedly asked PYQs (appeared 3+ times)
 * are ranked at the very top, followed by other relevant questions.
 */
export function sortQuestionsByFrequency(questions: PredictedQuestion[]): {
  highFrequency: PredictedQuestion[]
  relevant: PredictedQuestion[]
  allSorted: PredictedQuestion[]
} {
  const highFrequency: PredictedQuestion[] = []
  const relevant: PredictedQuestion[] = []

  for (const q of questions) {
    if (q.appeared.length >= 3) {
      highFrequency.push(q)
    } else {
      relevant.push(q)
    }
  }

  // Sort high-frequency questions by repeat count descending, then probability descending
  highFrequency.sort((a, b) => {
    if (b.appeared.length !== a.appeared.length) {
      return b.appeared.length - a.appeared.length
    }
    return b.probability - a.probability
  })

  // Sort relevant questions by probability descending
  relevant.sort((a, b) => b.probability - a.probability)

  return {
    highFrequency,
    relevant,
    allSorted: [...highFrequency, ...relevant],
  }
}

/**
 * Generates an on-the-fly subject object if the user enters a custom subject/topic name.
 */
export function buildCustomSubject(topicName: string): PaperSubject {
  const cleanName = topicName.trim()
  return {
    id: cleanName.toLowerCase().replace(/[^a-z0-9]/g, '-'),
    name: cleanName,
    code: 'MU-ENG',
    semester: 4,
    branch: 'Engineering Syllabus',
    accuracy: 89,
    questions: [
      {
        q: `Explain fundamental principles, architectural models, and core mechanisms of ${cleanName}.`,
        marks: 10,
        probability: 95,
        appeared: [2019, 2021, 2022, 2023, 2024],
        unit: 'Unit I / Core Theory',
        type: 'Theory',
      },
      {
        q: `Solve the standard analytical / design problem for ${cleanName} with step-by-step derivation.`,
        marks: 10,
        probability: 92,
        appeared: [2020, 2022, 2023, 2024],
        unit: 'Unit III / Numerical',
        type: 'Numerical',
      },
      {
        q: `Compare traditional methodologies versus modern approaches in ${cleanName} with performance tradeoffs.`,
        marks: 10,
        probability: 88,
        appeared: [2019, 2022, 2024],
        unit: 'Unit IV / Comparative',
        type: 'Theory',
      },
      {
        q: `Draw block diagram, flowchart, or state transition diagram illustrating real-world implementation of ${cleanName}.`,
        marks: 8,
        probability: 84,
        appeared: [2021, 2023, 2024],
        unit: 'Unit II / System Design',
        type: 'Diagram',
      },
      {
        q: `Short note on boundary conditions, failure modes, and industry standards related to ${cleanName}.`,
        marks: 5,
        probability: 73,
        appeared: [2022, 2024],
        unit: 'Unit V / Applications',
        type: 'Short note',
      },
    ],
  }
}
