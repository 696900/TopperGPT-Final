'use client'

import { useRef, useState } from 'react'
import { Markdown } from '@/components/markdown'
import { cn } from '@/lib/utils'
import {
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
      const content = await file.text()
      setText(content.slice(0, 12000))
    } else {
      setText(
        (prev) =>
          prev ||
          `[Uploaded document: ${file.name}. Paste the key text below so TopperGPT can synthesize precise notes, or type the topics this document covers.]`,
      )
    }
  }

  async function synthesize() {
    if (text.trim().length < 10) {
      setError('Add or paste at least a paragraph of study material.')
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
        body: JSON.stringify({ mode: 'notes', input: text }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed')
      setResult(data.text)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Synthesis failed.')
      setStatus('error')
    }
  }

  return (
    <div className="grid h-[calc(100svh-8.5rem)] min-h-[520px] grid-cols-1 gap-3 lg:grid-cols-2">
      {/* Input */}
      <section className="glass flex min-h-0 flex-col overflow-hidden rounded-2xl">
        <div className="flex items-center gap-2 border-b border-border/70 px-4 py-3">
          <NotebookPen className="size-4 text-cyan-neon" />
          <h3 className="text-sm font-semibold text-white">Source material</h3>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-3 p-4">
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
              'flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border border-dashed py-6 text-center transition-colors',
              dragging
                ? 'border-cyan-neon bg-cyan-neon/5'
                : 'border-border hover:border-cyan-neon/50',
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
            <UploadCloud className="size-6 text-cyan-neon" />
            <p className="text-sm font-medium text-white">
              Drop a PDF or document
            </p>
            <p className="text-xs text-muted-foreground">
              or click to browse — text files auto-load
            </p>
          </div>

          {fileName && (
            <div className="flex items-center gap-2 rounded-lg border border-cyan-neon/30 bg-cyan-neon/10 px-3 py-2 text-xs text-white">
              <FileText className="size-4 text-cyan-neon" />
              <span className="flex-1 truncate">{fileName}</span>
              <button
                onClick={() => {
                  setFileName(null)
                  setText('')
                }}
                aria-label="Remove file"
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="size-3.5" />
              </button>
            </div>
          )}

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="...or paste your lecture notes, textbook section, or PDF text here."
            className="scroll-thin min-h-0 flex-1 resize-none rounded-xl border border-border bg-secondary/40 p-3.5 text-sm leading-relaxed text-white outline-none placeholder:text-muted-foreground/70 focus:border-cyber"
          />

          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted-foreground">
              {text.length.toLocaleString()} chars
            </span>
            <button
              onClick={synthesize}
              disabled={status === 'working'}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === 'working' ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Synthesizing...
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
            <p className="text-xs text-destructive" role="alert">
              {error}
            </p>
          )}
        </div>
      </section>

      {/* Output */}
      <section className="glass flex min-h-0 flex-col overflow-hidden rounded-2xl">
        <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-academic" />
            <h3 className="text-sm font-semibold text-white">
              Structured summary
            </h3>
          </div>
          {status === 'done' && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(result)
                setCopied(true)
                setTimeout(() => setCopied(false), 1500)
              }}
              className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:text-white"
            >
              <Copy className="size-3" />
              {copied ? 'Copied' : 'Copy'}
            </button>
          )}
        </div>

        <div className="scroll-thin flex-1 overflow-y-auto p-4 sm:p-5">
          {status === 'working' ? (
            <div className="grid h-full place-items-center text-center">
              <div>
                <Loader2 className="mx-auto size-7 animate-spin text-cyber" />
                <p className="mt-3 text-sm text-muted-foreground">
                  Extracting concepts, formulas &amp; likely questions...
                </p>
              </div>
            </div>
          ) : status === 'done' ? (
            <Markdown content={result} />
          ) : (
            <div className="grid h-full place-items-center text-center">
              <div className="max-w-xs">
                <div className="mx-auto grid size-12 place-items-center rounded-xl bg-secondary">
                  <NotebookPen className="size-6 text-cyan-neon" />
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                  Your exam-ready summary with key concepts, formulas, and
                  probable questions will appear here.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
