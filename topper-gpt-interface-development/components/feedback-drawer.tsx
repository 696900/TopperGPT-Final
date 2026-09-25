'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import { CheckCircle2, Loader2, MessageSquarePlus, Star, X } from 'lucide-react'

const CATEGORIES = [
  'AI Tutor quality',
  'Paper prediction accuracy',
  'Notes synthesis',
  'UI / Performance',
  'Feature request',
  'Bug report',
] as const

type Status = 'idle' | 'submitting' | 'success' | 'error'

export function FeedbackDrawer({
  open,
  onClose,
  section,
}: {
  open: boolean
  onClose: () => void
  section: string
}) {
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [category, setCategory] = useState<string>(CATEGORIES[0])
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setStatus('idle')
      setError('')
    }
  }, [open])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    if (open) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  async function submit() {
    setError('')
    if (rating < 1) {
      setError('Please select a star rating.')
      return
    }
    if (message.trim().length < 3) {
      setError('Please write a short message.')
      return
    }
    setStatus('submitting')
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, category, message, section }),
      })
      const data = await res.json()
      if (!res.ok || !data.ok) throw new Error(data.error || 'Failed')
      setStatus('success')
      setRating(0)
      setMessage('')
      setCategory(CATEGORIES[0])
    } catch (e) {
      setStatus('error')
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    }
  }

  return (
    <div
      className={cn(
        'fixed inset-0 z-[60] transition',
        open ? 'pointer-events-auto' : 'pointer-events-none',
      )}
      aria-hidden={!open}
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={cn(
          'absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300',
          open ? 'opacity-100' : 'opacity-0',
        )}
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Send feedback"
        className={cn(
          'glass absolute right-0 top-0 flex h-full w-full max-w-md flex-col rounded-l-2xl transition-transform duration-300 ease-out sm:right-3 sm:top-3 sm:h-[calc(100%-1.5rem)] sm:rounded-2xl',
          open ? 'translate-x-0' : 'translate-x-[110%]',
        )}
      >
        <div className="flex items-center justify-between border-b border-border/70 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-cyber to-cyan-neon">
              <MessageSquarePlus className="size-5 text-white" />
            </div>
            <div>
              <h2 className="font-slab text-base font-bold text-white">
                Feedback &amp; Telemetry
              </h2>
              <p className="text-xs text-muted-foreground">
                Help us tune TopperGPT
              </p>
            </div>
          </div>
          <button
            aria-label="Close feedback"
            onClick={onClose}
            className="grid size-8 place-items-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-white"
          >
            <X className="size-4" />
          </button>
        </div>

        {status === 'success' ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
            <div className="grid size-16 place-items-center rounded-full bg-chart-5/15 text-chart-5">
              <CheckCircle2 className="size-9" />
            </div>
            <div>
              <h3 className="font-slab text-lg font-bold text-white">
                Feedback received
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Your input was ingested into our telemetry pipeline. Thank you
                for helping toppers everywhere.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setStatus('idle')}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-white hover:bg-secondary"
              >
                Send another
              </button>
              <button
                onClick={onClose}
                className="rounded-lg bg-gradient-to-r from-cyber to-cyan-neon px-4 py-2 text-sm font-semibold text-white"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <div className="scroll-thin flex-1 space-y-6 overflow-y-auto p-5">
            {/* Rating */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                Overall experience
              </label>
              <div className="flex items-center gap-1.5">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onMouseEnter={() => setHover(n)}
                    onMouseLeave={() => setHover(0)}
                    onClick={() => setRating(n)}
                    aria-label={`${n} star${n > 1 ? 's' : ''}`}
                    className="rounded-md p-1 transition-transform hover:scale-110"
                  >
                    <Star
                      className={cn(
                        'size-7 transition-colors',
                        (hover || rating) >= n
                          ? 'fill-academic text-academic'
                          : 'text-muted-foreground',
                      )}
                    />
                  </button>
                ))}
                {rating > 0 && (
                  <span className="ml-2 text-sm text-muted-foreground">
                    {rating}/5
                  </span>
                )}
              </div>
            </div>

            {/* Category */}
            <div>
              <label className="mb-2 block text-sm font-medium text-white">
                Category
              </label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setCategory(c)}
                    className={cn(
                      'rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
                      category === c
                        ? 'border-cyber bg-cyber/15 text-white'
                        : 'border-border text-muted-foreground hover:border-cyber/40 hover:text-white',
                    )}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            {/* Message */}
            <div>
              <label
                htmlFor="fb-message"
                className="mb-2 block text-sm font-medium text-white"
              >
                Your message
              </label>
              <textarea
                id="fb-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={5}
                placeholder="Tell us what worked, what didn't, or what you'd love to see next..."
                className="scroll-thin w-full resize-none rounded-xl border border-border bg-secondary/40 px-3.5 py-3 text-sm text-white outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-cyber"
              />
              <div className="mt-1 text-right text-[11px] text-muted-foreground">
                {message.length}/2000
              </div>
            </div>

            <div className="rounded-lg border border-border/70 bg-secondary/30 px-3 py-2.5 text-[11px] leading-relaxed text-muted-foreground">
              Context auto-attached:{' '}
              <span className="font-medium text-cyan-neon">
                section = {section}
              </span>
              . Submissions are sent to{' '}
              <code className="text-cyber">/api/feedback</code> for database
              ingestion.
            </div>

            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
          </div>
        )}

        {status !== 'success' && (
          <div className="border-t border-border/70 p-4">
            <button
              onClick={submit}
              disabled={status === 'submitting'}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyber to-cyan-neon py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === 'submitting' ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit feedback'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
