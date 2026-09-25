'use client'

import { useMemo, useState } from 'react'
import { SUBJECTS, type PredictedQuestion } from '@/lib/papers-data'
import { cn } from '@/lib/utils'
import {
  BarChart3,
  BrainCircuit,
  Check,
  ChevronDown,
  Download,
  Loader2,
  Target,
  TrendingUp,
} from 'lucide-react'

function probColor(p: number) {
  if (p >= 80) return 'text-chart-5'
  if (p >= 65) return 'text-academic'
  return 'text-muted-foreground'
}
function probBar(p: number) {
  if (p >= 80) return 'from-chart-5 to-chart-5/60'
  if (p >= 65) return 'from-academic to-academic/60'
  return 'from-cyber to-cyan-neon'
}

export function PredictedPapers() {
  const [subjectId, setSubjectId] = useState(SUBJECTS[0].id)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)

  const subject = useMemo(
    () => SUBJECTS.find((s) => s.id === subjectId)!,
    [subjectId],
  )

  const sorted = useMemo(
    () => [...subject.questions].sort((a, b) => b.probability - a.probability),
    [subject],
  )

  const avgProb = Math.round(
    subject.questions.reduce((s, q) => s + q.probability, 0) /
      subject.questions.length,
  )

  function generate() {
    setGenerating(true)
    setGenerated(false)
    setTimeout(() => {
      setGenerating(false)
      setGenerated(true)
    }, 1400)
  }

  return (
    <div className="scroll-thin h-[calc(100svh-8.5rem)] min-h-[520px] space-y-4 overflow-y-auto pr-1">
      {/* Controls */}
      <div className="glass rounded-2xl p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex-1">
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Select subject
            </label>
            <div className="relative max-w-md">
              <select
                value={subjectId}
                onChange={(e) => {
                  setSubjectId(e.target.value)
                  setGenerated(false)
                }}
                className="w-full appearance-none rounded-xl border border-border bg-secondary/50 px-4 py-3 pr-10 text-sm font-medium text-white outline-none focus:border-cyber"
              >
                {SUBJECTS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} — {s.code}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            </div>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>Sem {subject.semester}</span>
              <span>•</span>
              <span>{subject.branch}</span>
              <span>•</span>
              <span>Mumbai University</span>
            </div>
          </div>

          <button
            onClick={generate}
            disabled={generating}
            className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon px-5 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
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

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metric
          icon={<Target className="size-5 text-chart-5" />}
          value={`${subject.accuracy}%`}
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
          label="Papers analyzed"
        />
        <Metric
          icon={<Check className="size-5 text-academic" />}
          value={String(subject.questions.length)}
          label="High-yield questions"
        />
      </div>

      {/* Predictions */}
      {generating ? (
        <div className="glass grid place-items-center rounded-2xl py-20 text-center">
          <div>
            <Loader2 className="mx-auto size-8 animate-spin text-cyber" />
            <p className="mt-3 text-sm text-muted-foreground">
              Running frequency analysis &amp; pattern detection...
            </p>
          </div>
        </div>
      ) : generated ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="font-slab text-base font-bold text-white">
              Predicted high-yield questions
            </h3>
            <button className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white">
              <Download className="size-3.5" />
              Export PDF
            </button>
          </div>
          {sorted.map((q, i) => (
            <QuestionCard key={i} q={q} rank={i + 1} />
          ))}
        </div>
      ) : (
        <div className="glass grid place-items-center rounded-2xl py-20 text-center">
          <div className="max-w-sm">
            <div className="mx-auto grid size-12 place-items-center rounded-xl bg-secondary">
              <BrainCircuit className="size-6 text-cyber" />
            </div>
            <h3 className="mt-3 font-slab text-base font-bold text-white">
              Predict {subject.name}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Our engine analyzes 6 years of Mumbai University papers to forecast
              the most probable questions. Hit predict to begin.
            </p>
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

function QuestionCard({ q, rank }: { q: PredictedQuestion; rank: number }) {
  return (
    <div className="glass rounded-2xl p-4 transition-colors hover:border-cyber/40">
      <div className="flex items-start gap-3">
        <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-secondary font-slab text-sm font-bold text-cyber">
          {rank}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium leading-relaxed text-white">
            {q.q}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Tag>{q.unit}</Tag>
            <Tag>{q.type}</Tag>
            <Tag>{q.marks} marks</Tag>
            <span className="text-[11px] text-muted-foreground">
              Appeared: {q.appeared.join(', ')}
            </span>
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
                'w-24 text-right text-xs font-semibold',
                probColor(q.probability),
              )}
            >
              {q.probability}% likely
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
