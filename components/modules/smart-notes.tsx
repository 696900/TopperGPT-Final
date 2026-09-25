'use client'

import { useRef, useState } from 'react'
import { Markdown } from '@/components/markdown'
import { cn } from '@/lib/utils'
import {
  BookOpen,
  Copy,
  FileText,
  Loader2,
  NotebookPen,
  Sparkles,
  UploadCloud,
  Wand2,
  X,
} from 'lucide-react'

type Status = 'idle' | 'working' | 'done' | 'error'

const QUICK_TOPICS = [
  "Banker's Algorithm & Deadlocks",
  'AVL Tree Rotations & Balancing',
  'Laplace Transforms & Convolution',
  'BCNF & Normalization in DBMS',
  'TCP 3-Way Handshake & Congestion Control',
  '8086 BIU & EU Architecture',
]

export function SmartNotes() {
  const [text, setText] = useState('')
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState('')
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function readFile(file: File) {
    setFileName(file.name)
    const isText =
      file.type.startsWith('text') ||
      /\.(txt|md|csv|json)$/i.test(file.name)
    if (isText) {
      try {
        const content = await file.text()
        setText(content.slice(0, 12000))
      } catch {
        setText(
          (prev) =>
            prev ||
            `[Attached File: ${file.name}]\nEnter topic details or prompt below to synthesize structured exam notes.`,
        )
      }
    } else {
      setText(
        (prev) =>
          prev ||
          `[Attached File: ${file.name}]\nTopic: ${file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')}`,
      )
    }
  }

  async function synthesize() {
    const trimmed = text.trim()
    // PDF upload is optional! User can simply type a topic name or paste text.
    if (!trimmed) {
      setError('Please type a topic name (e.g. "Deadlocks in OS") or paste study material.')
      setStatus('error')
      return
    }

    setStatus('working')
    setError('')
    setResult('')
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: 'notes',
          input: trimmed,
          fileName: fileName || undefined,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Synthesis failed')
      setResult(data.text)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Synthesis failed. Please try again.')
      setStatus('error')
    }
  }

  return (
    <div className="grid h-[calc(100svh-8.5rem)] min-h-[520px] grid-cols-1 gap-3 lg:grid-cols-2">
      {/* Input Section */}
      <section className="glass flex min-h-0 flex-col overflow-hidden rounded-2xl">
        <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
          <div className="flex items-center gap-2">
            <NotebookPen className="size-4 text-cyan-neon" />
            <h3 className="text-sm font-semibold text-white">Source Material or Topic</h3>
          </div>
          <span className="rounded-full border border-cyber/30 bg-cyber/10 px-2 py-0.5 text-[10px] font-medium text-cyan-neon">
            PDF Upload Optional
          </span>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-3 p-4">
          {/* Optional File Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              if (e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0])
            }}
            onClick={() => fileRef.current?.click()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border border-dashed py-4 text-center transition-colors',
              dragging
                ? 'border-cyan-neon bg-cyan-neon/5'
                : 'border-border/80 hover:border-cyan-neon/50 bg-secondary/20',
            )}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt,.md,.doc,.docx,.csv,.json"
              className="hidden"
              onChange={(e) =>
                e.target.files?.[0] && readFile(e.target.files[0])
              }
            />
            <UploadCloud className="size-5 text-cyan-neon" />
            <p className="text-xs font-medium text-white">
              Drop a PDF or document <span className="text-muted-foreground font-normal">(Optional)</span>
            </p>
            <p className="text-[11px] text-muted-foreground">
              or skip file upload and directly type your topic or notes below
            </p>
          </div>

          {/* Attached File Pill if any */}
          {fileName && (
            <div className="flex items-center gap-2 rounded-lg border border-cyan-neon/30 bg-cyan-neon/10 px-3 py-2 text-xs text-white">
              <FileText className="size-4 text-cyan-neon shrink-0" />
              <span className="flex-1 truncate font-medium">{fileName}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setFileName(null)
                }}
                aria-label="Remove attached file"
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="size-3.5" />
              </button>
            </div>
          )}

          {/* Topic / Text Direct Input */}
          <div className="flex min-h-0 flex-1 flex-col gap-1.5">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type your topic name directly (e.g. 'Banker\\'s Algorithm in OS', 'AVL Tree Rotations', 'Laplace Transforms') or paste textbook text / lecture notes here..."
              className="scroll-thin min-h-[120px] flex-1 resize-none rounded-xl border border-border bg-secondary/40 p-3.5 text-sm leading-relaxed text-white outline-none placeholder:text-muted-foreground/60 focus:border-cyber focus:ring-1 focus:ring-cyber/30"
            />

            {/* Quick Topic Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                <BookOpen className="size-3 text-cyber" />
                Quick topics:
              </span>
              {QUICK_TOPICS.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => setText(topic)}
                  className="rounded-md border border-border/70 bg-secondary/50 px-2 py-0.5 text-[11px] text-muted-foreground transition-colors hover:border-cyber/60 hover:text-white"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between gap-3 pt-1">
            <span className="text-xs text-muted-foreground">
              {text.length.toLocaleString()} chars entered
            </span>
            <button
              onClick={synthesize}
              disabled={status === 'working'}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyber/20 transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === 'working' ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Synthesizing Notes...
                </>
              ) : (
                <>
                  <Wand2 className="size-4" />
                  Synthesize notes
                </>
              )}
            </button>
          </div>

          {status === 'error' && (
            <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive" role="alert">
              {error}
            </p>
          )}
        </div>
      </section>

      {/* Output Section */}
      <section className="glass flex min-h-0 flex-col overflow-hidden rounded-2xl">
        <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-academic" />
            <h3 className="text-sm font-semibold text-white">
              Structured Exam-Ready Notes
            </h3>
          </div>
          {status === 'done' && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(result)
                setCopied(true)
                setTimeout(() => setCopied(false), 1500)
              }}
              className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white"
            >
              <Copy className="size-3" />
              {copied ? 'Copied to clipboard' : 'Copy notes'}
            </button>
          )}
        </div>

        <div className="scroll-thin flex-1 overflow-y-auto p-4 sm:p-5">
          {status === 'working' ? (
            <div className="grid h-full place-items-center text-center">
              <div>
                <Loader2 className="mx-auto size-8 animate-spin text-cyber" />
                <p className="mt-3 text-sm font-medium text-white">
                  Synthesizing high-yield short notes...
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Formulating TL;DR, key definitions, formulas, and Mumbai University probable questions
                </p>
              </div>
            </div>
          ) : status === 'done' ? (
            <div className="prose prose-invert max-w-none">
              <Markdown content={result} />
            </div>
          ) : (
            <div className="grid h-full place-items-center text-center">
              <div className="max-w-xs">
                <div className="mx-auto grid size-12 place-items-center rounded-xl bg-secondary">
                  <NotebookPen className="size-6 text-cyan-neon" />
                </div>
                <h4 className="mt-3 font-slab text-sm font-bold text-white">
                  Exam Notes Generator Ready
                </h4>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                  Type any engineering topic name or paste notes on the left. No PDF upload required! Your structured summary will appear here.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
