'use client'

import { useMemo, useState, useRef, useEffect } from 'react'
import {
  SUBJECTS,
  searchSubjects,
  sortQuestionsByFrequency,
  buildCustomSubject,
  type PaperSubject,
  type PredictedQuestion,
} from '@/lib/papers-data'
import { cn } from '@/lib/utils'
import {
  BarChart3,
  BrainCircuit,
  Check,
  Download,
  Flame,
  HelpCircle,
  History,
  Layers,
  Loader2,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from 'lucide-react'

function probColor(p: number) {
  if (p >= 90) return 'text-chart-5'
  if (p >= 80) return 'text-cyan-neon'
  if (p >= 70) return 'text-academic'
  return 'text-muted-foreground'
}

function probBar(p: number) {
  if (p >= 90) return 'from-chart-5 to-chart-5/70'
  if (p >= 80) return 'from-cyan-neon to-cyber'
  if (p >= 70) return 'from-academic to-academic/70'
  return 'from-cyber to-cyan-neon'
}

export function PredictedPapers() {
  const [selectedSubject, setSelectedSubject] = useState<PaperSubject>(SUBJECTS[0])
  const [query, setQuery] = useState(SUBJECTS[0].name)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Filter subjects based on user search input
  const searchResults = useMemo(() => {
    return searchSubjects(query)
  }, [query])

  // Partition questions: High-frequency repeated PYQs (appeared 3+ times) at top, followed by relevant questions
  const { highFrequency, relevant, allSorted } = useMemo(() => {
    return sortQuestionsByFrequency(selectedSubject.questions)
  }, [selectedSubject])

  const avgProb = useMemo(() => {
    if (selectedSubject.questions.length === 0) return 0
    return Math.round(
      selectedSubject.questions.reduce((s, q) => s + q.probability, 0) /
        selectedSubject.questions.length,
    )
  }, [selectedSubject])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleSelect(s: PaperSubject) {
    setSelectedSubject(s)
    setQuery(s.name)
    setIsDropdownOpen(false)
    setGenerated(false)
  }

  function handleCustomSearchSubmit() {
    setIsDropdownOpen(false)
    const exact = SUBJECTS.find(
      (s) =>
        s.name.toLowerCase() === query.trim().toLowerCase() ||
        s.code.toLowerCase() === query.trim().toLowerCase(),
    )
    if (exact) {
      setSelectedSubject(exact)
    } else if (searchResults.length > 0) {
      setSelectedSubject(searchResults[0])
    } else if (query.trim().length > 0) {
      setSelectedSubject(buildCustomSubject(query.trim()))
    }
    setGenerated(false)
  }

  function generate() {
    setGenerating(true)
    setGenerated(false)
    setTimeout(() => {
      setGenerating(false)
      setGenerated(true)
    }, 1200)
  }

  return (
    <div className="scroll-thin h-[calc(100svh-8.5rem)] min-h-[520px] space-y-4 overflow-y-auto pr-1">
      {/* Controls & Search Box */}
      <div className="glass rounded-2xl p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="relative flex-1" ref={dropdownRef}>
            <label className="mb-1.5 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Search Mumbai University Subject</span>
              <span className="text-[11px] font-normal lowercase tracking-normal text-cyan-neon">
                Type subject name, code, or topic
              </span>
            </label>

            {/* Dynamic Search / Type Input */}
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center">
                <Search className="size-4 text-cyber" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value)
                  setIsDropdownOpen(true)
                  setGenerated(false)
                }}
                onFocus={() => setIsDropdownOpen(true)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCustomSearchSubmit()
                  }
                }}
                placeholder="e.g. Data Structures, Operating Systems, FEC301, Maths, DBMS..."
                className="w-full rounded-xl border border-border bg-secondary/60 py-3 pl-10 pr-10 text-sm font-medium text-white outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-cyber focus:ring-1 focus:ring-cyber/30"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery('')
                    setIsDropdownOpen(true)
                  }}
                  className="absolute inset-y-0 right-3 flex items-center text-muted-foreground hover:text-white"
                >
                  <X className="size-4" />
                </button>
              )}
            </div>

            {/* Autocomplete Suggestions Dropdown */}
            {isDropdownOpen && (
              <div className="scroll-thin absolute left-0 right-0 z-50 mt-1.5 max-h-72 overflow-y-auto rounded-xl border border-border bg-[#0c0d12]/95 p-1.5 shadow-2xl backdrop-blur-xl">
                {searchResults.length > 0 ? (
                  searchResults.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => handleSelect(s)}
                      className={cn(
                        'flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-xs transition-colors hover:bg-secondary',
                        s.id === selectedSubject.id && 'bg-secondary/70 text-white font-semibold',
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-medium text-white">{s.name}</span>
                          <span className="rounded border border-cyber/30 bg-cyber/10 px-1.5 py-0.5 text-[10px] font-mono text-cyan-neon">
                            {s.code}
                          </span>
                        </div>
                        <div className="mt-0.5 text-[11px] text-muted-foreground">
                          Sem {s.semester} • {s.branch} • Mumbai Univ.
                        </div>
                      </div>
                      <span className="shrink-0 text-[11px] font-medium text-chart-5">
                        {s.accuracy}% accuracy
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="p-3 text-center">
                    <p className="text-xs text-muted-foreground">
                      No exact match in indexed list. Press Enter to predict for:
                    </p>
                    <button
                      type="button"
                      onClick={handleCustomSearchSubmit}
                      className="mt-1.5 inline-flex items-center gap-1.5 rounded-lg border border-cyber/40 bg-cyber/10 px-3 py-1.5 text-xs font-semibold text-cyber hover:bg-cyber/20"
                    >
                      <Sparkles className="size-3.5" />
                      Predict questions for "{query}"
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Subject details & quick filter chips */}
            <div className="mt-2.5 flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-muted-foreground">Quick pick:</span>
              {SUBJECTS.slice(0, 5).map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => handleSelect(s)}
                  className={cn(
                    'rounded-md border px-2 py-0.5 text-[11px] transition-colors',
                    selectedSubject.id === s.id
                      ? 'border-cyber bg-cyber/15 text-white font-medium'
                      : 'border-border/80 bg-secondary/40 text-muted-foreground hover:border-cyber/50 hover:text-white',
                  )}
                >
                  {s.name.split(' ')[0]} ({s.code})
                </button>
              ))}
            </div>

            {/* Selected Subject Badges */}
            <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
              <span className="font-medium text-white">{selectedSubject.name}</span>
              <span>•</span>
              <span className="text-cyan-neon font-mono">{selectedSubject.code}</span>
              <span>•</span>
              <span>Sem {selectedSubject.semester}</span>
              <span>•</span>
              <span>{selectedSubject.branch}</span>
              <span>•</span>
              <span>Mumbai University (Rev-2019/2024 'C' Scheme)</span>
            </div>
          </div>

          <button
            onClick={generate}
            disabled={generating}
            className="flex shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-cyber/20 transition-all hover:opacity-90 disabled:opacity-60"
          >
            {generating ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analyzing 6 years of papers...
              </>
            ) : (
              <>
                <BrainCircuit className="size-4" />
                Predict question paper
              </>
            )}
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metric
          icon={<Target className="size-5 text-chart-5" />}
          value={`${selectedSubject.accuracy}%`}
          label="Predictor accuracy"
        />
        <Metric
          icon={<TrendingUp className="size-5 text-cyber" />}
          value={`${avgProb}%`}
          label="Avg. appearance likelihood"
        />
        <Metric
          icon={<BarChart3 className="size-5 text-cyan-neon" />}
          value="6 yrs"
          label="Papers analyzed (2019-2024)"
        />
        <Metric
          icon={<Flame className="size-5 text-academic" />}
          value={String(highFrequency.length)}
          label="High-frequency repeat PYQs"
        />
      </div>

      {/* Predictions Content */}
      {generating ? (
        <div className="glass grid place-items-center rounded-2xl py-20 text-center">
          <div className="max-w-md">
            <Loader2 className="mx-auto size-9 animate-spin text-cyber" />
            <h4 className="mt-4 font-slab text-base font-bold text-white">
              Running Frequency Analysis &amp; Pattern Matching
            </h4>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              Scanning Mumbai University previous 6 years' exam papers (May/Dec 2019 to 2024) to isolate high-frequency repeat patterns for {selectedSubject.name}...
            </p>
          </div>
        </div>
      ) : generated ? (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-1">
            <div>
              <h3 className="font-slab text-lg font-bold text-white">
                Predicted Questions: {selectedSubject.name} ({selectedSubject.code})
              </h3>
              <p className="text-xs text-muted-foreground">
                Showing {allSorted.length} predicted questions based on 6 years of Mumbai University exam patterns.
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white"
            >
              <Download className="size-3.5" />
              Export PDF
            </button>
          </div>

          {/* SECTION 1: High-Frequency Repeated PYQs (AT THE TOP) */}
          {highFrequency.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 rounded-xl border border-academic/40 bg-gradient-to-r from-academic/15 to-transparent px-3 py-2">
                <Flame className="size-4 text-academic" />
                <div>
                  <h4 className="font-slab text-sm font-bold text-white">
                    Most Repeated Questions (High-Frequency PYQs — Appeared in 3+ Papers)
                  </h4>
                  <p className="text-[11px] text-muted-foreground">
                    These questions have recurred repeatedly across Mumbai University exam cycles and carry the highest probability.
                  </p>
                </div>
              </div>

              {highFrequency.map((q, i) => (
                <QuestionCard key={`high-${i}`} q={q} rank={i + 1} isHighFrequency />
              ))}
            </div>
          )}

          {/* SECTION 2: All Relevant Questions for this Topic */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 rounded-xl border border-border/80 bg-secondary/40 px-3 py-2">
              <Layers className="size-4 text-cyan-neon" />
              <div>
                <h4 className="font-slab text-sm font-bold text-white">
                  Relevant Topic Questions &amp; Syllabus Predictions
                </h4>
                <p className="text-[11px] text-muted-foreground">
                  Additional high-yield questions for comprehensive unit-wise exam preparation.
                </p>
              </div>
            </div>

            {relevant.map((q, i) => (
              <QuestionCard
                key={`rel-${i}`}
                q={q}
                rank={highFrequency.length + i + 1}
                isHighFrequency={false}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="glass grid place-items-center rounded-2xl py-20 text-center">
          <div className="max-w-md">
            <div className="mx-auto grid size-12 place-items-center rounded-xl bg-secondary">
              <BrainCircuit className="size-6 text-cyber" />
            </div>
            <h3 className="mt-3 font-slab text-base font-bold text-white">
              Predict {selectedSubject.name}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Our frequency engine analyzes 6 years of Mumbai University past examination papers to isolate recurring questions and forecast likely exam prompts.
            </p>
            <button
              onClick={generate}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon px-5 py-2.5 text-xs font-semibold text-white shadow-md transition-opacity hover:opacity-90"
            >
              <BrainCircuit className="size-4" />
              Predict question paper
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Metric({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode
  value: string
  label: string
}) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="mb-2">{icon}</div>
      <div className="font-slab text-2xl font-bold text-white">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

function QuestionCard({
  q,
  rank,
  isHighFrequency,
}: {
  q: PredictedQuestion
  rank: number
  isHighFrequency: boolean
}) {
  const repeatCount = q.appeared.length

  return (
    <div
      className={cn(
        'glass rounded-2xl p-4 transition-all hover:border-cyber/50',
        isHighFrequency && 'border-academic/30 bg-gradient-to-r from-academic/5 via-transparent to-transparent',
      )}
    >
      <div className="flex items-start gap-3.5">
        <div
          className={cn(
            'grid size-8 shrink-0 place-items-center rounded-lg font-slab text-sm font-bold',
            isHighFrequency
              ? 'bg-academic/20 text-academic shadow-sm'
              : 'bg-secondary text-cyber',
          )}
        >
          {rank}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {isHighFrequency ? (
              <span className="inline-flex items-center gap-1 rounded-md border border-academic/40 bg-academic/15 px-2 py-0.5 text-[11px] font-semibold text-academic">
                <Flame className="size-3" />
                Repeated {repeatCount}x in MU PYQs
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-md border border-border bg-secondary/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                <History className="size-3" />
                Appeared {repeatCount}x
              </span>
            )}
            <Tag>{q.unit}</Tag>
            <Tag>{q.type}</Tag>
            <Tag>{q.marks} marks</Tag>
          </div>

          <p className="mt-2 text-sm font-medium leading-relaxed text-white">
            {q.q}
          </p>

          <div className="mt-2.5 flex items-center gap-1 text-[11px] text-muted-foreground">
            <span>Exam appearances:</span>
            <span className="font-mono text-white/90">{q.appeared.join(', ')}</span>
          </div>

          <div className="mt-3 flex items-center gap-3">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
              <div
                className={cn(
                  'h-full rounded-full bg-gradient-to-r transition-all',
                  probBar(q.probability),
                )}
                style={{ width: `${q.probability}%` }}
              />
            </div>
            <span
              className={cn(
                'w-28 text-right text-xs font-semibold',
                probColor(q.probability),
              )}
            >
              {q.probability}% probability
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-md border border-border bg-secondary/50 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
      {children}
    </span>
  )
}
