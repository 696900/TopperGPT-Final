'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { Markdown } from '@/components/markdown'
import { analyzeQuery, type GuardrailStatus } from '@/lib/guardrail'
import { cn } from '@/lib/utils'
import {
  ArrowUp,
  Bot,
  FileText,
  Gauge,
  Paperclip,
  ShieldCheck,
  Sparkles,
  Square,
  Trash2,
  UploadCloud,
  User,
} from 'lucide-react'

const SUGGESTIONS = [
  'Derive the transfer function of an RC low-pass filter',
  'Explain time complexity of quicksort with an example',
  'Summarize the laws of thermodynamics for my exam',
  'Write Dijkstra’s algorithm in Python with comments',
]

const GUARD_STYLES: Record<
  GuardrailStatus,
  { dot: string; text: string; ring: string }
> = {
  idle: {
    dot: 'bg-muted-foreground',
    text: 'text-muted-foreground',
    ring: 'border-border',
  },
  academic: {
    dot: 'bg-chart-5',
    text: 'text-chart-5',
    ring: 'border-chart-5/40',
  },
  borderline: {
    dot: 'bg-academic',
    text: 'text-academic',
    ring: 'border-academic/40',
  },
  offtopic: {
    dot: 'bg-destructive',
    text: 'text-destructive',
    ring: 'border-destructive/40',
  },
}

function textOf(message: { parts: Array<{ type: string; text?: string }> }) {
  return message.parts
    .filter((p) => p.type === 'text')
    .map((p) => p.text ?? '')
    .join('')
}

export function AiTutor() {
  const { messages, sendMessage, status, stop, setMessages } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  })

  const [input, setInput] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const busy = status === 'submitted' || status === 'streaming'
  const guard = useMemo(() => analyzeQuery(input), [input])

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, busy])

  function handleSubmit() {
    const trimmed = input.trim()
    if (!trimmed || busy) return
    const attachNote =
      files.length > 0
        ? `\n\n[Attached documents for context: ${files
            .map((f) => f.name)
            .join(', ')}]`
        : ''
    sendMessage({ text: trimmed + attachNote })
    setInput('')
    setFiles([])
  }

  function addFiles(list: FileList | null) {
    if (!list) return
    setFiles((prev) => [...prev, ...Array.from(list)].slice(0, 4))
  }

  return (
    <div className="grid h-[calc(100svh-8.5rem)] min-h-[520px] grid-cols-1 gap-3 xl:grid-cols-[1fr_300px]">
      {/* Chat column */}
      <section className="glass flex min-h-0 flex-col overflow-hidden rounded-2xl">
        {/* Messages */}
        <div
          ref={scrollRef}
          className="scroll-thin relative flex-1 space-y-6 overflow-y-auto p-4 sm:p-6"
        >
          {messages.length === 0 ? (
            <EmptyState
              onPick={(s) => setInput(s)}
              disabled={busy}
            />
          ) : (
            messages.map((m) => (
              <MessageBubble
                key={m.id}
                role={m.role}
                text={textOf(m)}
                streaming={
                  busy && m === messages[messages.length - 1] && m.role === 'assistant'
                }
              />
            ))
          )}
          {status === 'submitted' &&
            messages[messages.length - 1]?.role === 'user' && (
              <MessageBubble role="assistant" text="" streaming />
            )}
        </div>

        {/* Composer */}
        <div className="border-t border-border/70 p-3 sm:p-4">
          {/* Guardrail bar */}
          <div
            className={cn(
              'mb-2 flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs transition-colors',
              GUARD_STYLES[guard.status].ring,
            )}
          >
            <ShieldCheck
              className={cn('size-3.5', GUARD_STYLES[guard.status].text)}
            />
            <span className={cn('font-semibold', GUARD_STYLES[guard.status].text)}>
              {guard.label}
            </span>
            <span className="truncate text-muted-foreground">{guard.hint}</span>
          </div>

          {/* Attachment chips */}
          {files.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {files.map((f, i) => (
                <span
                  key={`${f.name}-${i}`}
                  className="flex items-center gap-1.5 rounded-lg border border-cyan-neon/30 bg-cyan-neon/10 px-2.5 py-1 text-xs text-white"
                >
                  <FileText className="size-3.5 text-cyan-neon" />
                  <span className="max-w-[140px] truncate">{f.name}</span>
                  <button
                    onClick={() =>
                      setFiles((prev) => prev.filter((_, idx) => idx !== i))
                    }
                    aria-label={`Remove ${f.name}`}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="size-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Input + dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              addFiles(e.dataTransfer.files)
            }}
            className={cn(
              'relative flex items-end gap-2 rounded-xl border bg-secondary/40 p-2 transition-colors',
              dragging ? 'border-cyan-neon bg-cyan-neon/5' : 'border-border',
            )}
          >
            {dragging && (
              <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-xl bg-background/80 text-sm font-medium text-cyan-neon">
                <UploadCloud className="size-5" />
                Drop PDF / documents to add context
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md,.pptx"
              className="hidden"
              onChange={(e) => addFiles(e.target.files)}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              aria-label="Attach documents"
              className="grid size-9 shrink-0 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-cyan-neon"
            >
              <Paperclip className="size-5" />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (
                  e.key === 'Enter' &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing &&
                  e.keyCode !== 229
                ) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              rows={1}
              placeholder="Ask TopperGPT anything academic — concepts, code, derivations, exam prep..."
              className="scroll-thin max-h-40 min-h-[2.25rem] flex-1 resize-none bg-transparent py-2 text-sm text-white outline-none placeholder:text-muted-foreground/70"
            />

            {busy ? (
              <button
                onClick={stop}
                aria-label="Stop generating"
                className="grid size-9 shrink-0 place-items-center rounded-lg bg-secondary text-white transition-colors hover:bg-destructive/80"
              >
                <Square className="size-4 fill-current" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!input.trim()}
                aria-label="Send message"
                className="grid size-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-cyber to-cyan-neon text-white transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                <ArrowUp className="size-5" />
              </button>
            )}
          </div>
          <p className="mt-2 px-1 text-[11px] text-muted-foreground">
            TopperGPT can make mistakes. Verify critical formulas and results.
          </p>
        </div>
      </section>

      {/* Telemetry column */}
      <aside className="hidden min-h-0 flex-col gap-3 xl:flex">
        <div className="glass rounded-2xl p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
            <Gauge className="size-4 text-cyber" />
            Live Analytics
          </div>
          <div className="space-y-2.5">
            <Stat
              icon={<Bot className="size-4 text-cyber" />}
              label="Messages"
              value={String(messages.length)}
            />
            <Stat
              icon={<Sparkles className="size-4 text-cyan-neon" />}
              label="Model"
              value="gpt-5-mini"
            />
            <Stat
              icon={<ShieldCheck className="size-4 text-chart-5" />}
              label="Syllabus Mode"
              value="Mumbai Univ."
            />
          </div>
        </div>

        <div className="glass rounded-2xl p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
            <ShieldCheck className="size-4 text-chart-5" />
            Contextual Guardrail
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Every query is analyzed in real time to keep answers on academics
            and engineering. Off-syllabus prompts are redirected gracefully.
          </p>
          <div
            className={cn(
              'mt-3 flex items-center gap-2 rounded-lg border px-3 py-2 text-xs',
              GUARD_STYLES[guard.status].ring,
            )}
          >
            <span
              className={cn(
                'size-2 rounded-full',
                GUARD_STYLES[guard.status].dot,
              )}
            />
            <span className={cn('font-medium', GUARD_STYLES[guard.status].text)}>
              {guard.label}
            </span>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="glass flex items-center justify-center gap-2 rounded-2xl py-3 text-xs font-medium text-muted-foreground transition-colors hover:text-destructive"
          >
            <Trash2 className="size-4" />
            Clear conversation
          </button>
        )}
      </aside>
    </div>
  )
}

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border/60 bg-secondary/30 px-3 py-2">
      <span className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        {label}
      </span>
      <span className="text-sm font-semibold text-white">{value}</span>
    </div>
  )
}

function MessageBubble({
  role,
  text,
  streaming,
}: {
  role: string
  text: string
  streaming?: boolean
}) {
  const isUser = role === 'user'
  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'grid size-8 shrink-0 place-items-center rounded-lg',
          isUser
            ? 'bg-secondary text-muted-foreground'
            : 'bg-gradient-to-br from-cyber to-cyan-neon text-white',
        )}
      >
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'rounded-tr-sm bg-secondary text-white'
            : 'rounded-tl-sm border border-border/60 bg-card/60',
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap leading-relaxed">{text}</p>
        ) : text ? (
          <Markdown content={text} />
        ) : (
          <span className="typing-caret text-muted-foreground">
            TopperGPT is thinking
          </span>
        )}
        {!isUser && streaming && text && (
          <span className="typing-caret" aria-hidden />
        )}
      </div>
    </div>
  )
}

function EmptyState({
  onPick,
  disabled,
}: {
  onPick: (s: string) => void
  disabled: boolean
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 text-center">
      <div className="grid size-14 place-items-center rounded-2xl bg-gradient-to-br from-cyber to-cyan-neon glow-cyber">
        <Bot className="size-7 text-white" />
      </div>
      <h2 className="mt-4 font-slab text-xl font-bold text-white">
        Your AI Tutor is ready
      </h2>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">
        Ask concepts, request derivations, debug code, or drop a PDF for
        context. TopperGPT keeps every answer academically rigorous.
      </p>
      <div className="mt-6 grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            disabled={disabled}
            onClick={() => onPick(s)}
            className="group rounded-xl border border-border/70 bg-secondary/30 px-3.5 py-3 text-left text-xs text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white"
          >
            <Sparkles className="mb-1.5 size-4 text-cyan-neon" />
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
