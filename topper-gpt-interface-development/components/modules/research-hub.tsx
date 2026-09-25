'use client'

import { useState } from 'react'
import { Markdown } from '@/components/markdown'
import { cn } from '@/lib/utils'
import { Compass, Loader2, Search, Sparkles } from 'lucide-react'

const POPULAR = [
  'Convolutional Neural Networks',
  'Kirchhoff’s Laws',
  'TCP/IP protocol stack',
  'Normalization in DBMS',
  'Fourier Transform',
  'Process synchronization',
]

type Status = 'idle' | 'working' | 'done' | 'error'

export function ResearchHub() {
  const [topic, setTopic] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState('')
  const [activeTopic, setActiveTopic] = useState('')
  const [error, setError] = useState('')

  async function research(input: string) {
    const q = input.trim()
    if (q.length < 3) {
      setError('Enter a topic to research.')
      setStatus('error')
      return
    }
    setActiveTopic(q)
    setStatus('working')
    setError('')
    setResult('')
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'research', input: q }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed')
      setResult(data.text)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Research failed.')
      setStatus('error')
    }
  }

  return (
    <div className="scroll-thin h-[calc(100svh-8.5rem)] min-h-[520px] space-y-4 overflow-y-auto pr-1">
      <div className="glass rounded-2xl p-4 sm:p-5">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-3 py-2 focus-within:border-cyber">
          <Search className="size-5 text-muted-foreground" />
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => {
              if (
                e.key === 'Enter' &&
                !e.nativeEvent.isComposing &&
                e.keyCode !== 229
              ) {
                research(topic)
              }
            }}
            placeholder="Research any concept — e.g. 'Dynamic programming' or 'Thevenin's theorem'"
            className="flex-1 bg-transparent py-1.5 text-sm text-white outline-none placeholder:text-muted-foreground/70"
          />
          <button
            onClick={() => research(topic)}
            disabled={status === 'working'}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-cyber to-cyan-neon px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {status === 'working' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Compass className="size-4" />
            )}
            Explore
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">Trending:</span>
          {POPULAR.map((t) => (
            <button
              key={t}
              onClick={() => {
                setTopic(t)
                research(t)
              }}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white"
            >
              {t}
            </button>
          ))}
        </div>
        {status === 'error' && (
          <p className="mt-2 text-xs text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>

      <div className={cn('glass rounded-2xl', status === 'done' && 'p-5 sm:p-6')}>
        {status === 'working' ? (
          <div className="grid place-items-center py-20 text-center">
            <div>
              <Loader2 className="mx-auto size-8 animate-spin text-cyber" />
              <p className="mt-3 text-sm text-muted-foreground">
                Building a learning path for{' '}
                <span className="text-white">{activeTopic}</span>...
              </p>
            </div>
          </div>
        ) : status === 'done' ? (
          <>
            <div className="mb-4 flex items-center gap-2 border-b border-border/70 pb-3">
              <Sparkles className="size-4 text-academic" />
              <h3 className="font-slab text-base font-bold text-white">
                {activeTopic}
              </h3>
            </div>
            <Markdown content={result} />
          </>
        ) : (
          <div className="grid place-items-center py-20 text-center">
            <div className="max-w-sm">
              <div className="mx-auto grid size-12 place-items-center rounded-xl bg-secondary">
                <Compass className="size-6 text-cyber" />
              </div>
              <h3 className="mt-3 font-slab text-base font-bold text-white">
                Deep-dive any topic
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Get a curated learning path with prerequisites, core concepts,
                pitfalls, and practice — generated for engineering students.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
