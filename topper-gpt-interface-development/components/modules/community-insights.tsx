'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  ArrowBigUp,
  Award,
  Flame,
  MessageCircle,
  MessageSquarePlus,
  Share2,
  TrendingUp,
  Users,
} from 'lucide-react'

const TRENDING = [
  {
    tag: 'Operating Systems',
    q: 'Why does the Banker’s algorithm avoid deadlock but not prevent it?',
    author: 'riya_k',
    replies: 42,
    votes: 318,
    hot: true,
  },
  {
    tag: 'DSA',
    q: 'Cleanest way to detect a cycle in a directed graph for the exam?',
    author: 'arjun.dev',
    replies: 27,
    votes: 210,
    hot: true,
  },
  {
    tag: 'Maths III',
    q: 'Trick to remember Laplace transform of standard functions?',
    author: 'sneha_m',
    replies: 61,
    votes: 405,
    hot: false,
  },
  {
    tag: 'DBMS',
    q: 'Is 3NF always enough or should I aim for BCNF in Mumbai Univ papers?',
    author: 'the_topper',
    replies: 18,
    votes: 147,
    hot: false,
  },
]

const LEADERBOARD = [
  { name: 'Aditya S.', points: 12840, badge: 'Grandmaster' },
  { name: 'Priya N.', points: 11390, badge: 'Master' },
  { name: 'Kabir R.', points: 9925, badge: 'Master' },
  { name: 'Meera J.', points: 8710, badge: 'Expert' },
]

const STATS = [
  { icon: Users, value: '42,180', label: 'Active learners' },
  { icon: MessageCircle, value: '128k', label: 'Doubts solved' },
  { icon: TrendingUp, value: '96%', label: 'Avg. pass rate' },
]

export function CommunityInsights({
  onOpenFeedback,
}: {
  onOpenFeedback: () => void
}) {
  const [votes, setVotes] = useState<Record<number, number>>({})
  const [voted, setVoted] = useState<Record<number, boolean>>({})

  function toggleVote(i: number, base: number) {
    setVoted((v) => {
      const next = { ...v, [i]: !v[i] }
      setVotes((prev) => ({
        ...prev,
        [i]: base + (next[i] ? 1 : 0),
      }))
      return next
    })
  }

  return (
    <div className="scroll-thin h-[calc(100svh-8.5rem)] min-h-[520px] space-y-4 overflow-y-auto pr-1">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {STATS.map((s) => (
          <div key={s.label} className="glass rounded-xl p-4">
            <s.icon className="mb-2 size-5 text-cyan-neon" />
            <div className="font-slab text-xl font-bold text-white sm:text-2xl">
              {s.value}
            </div>
            <div className="text-xs text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_300px]">
        {/* Trending feed */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <Flame className="size-4 text-academic" />
            <h3 className="font-slab text-base font-bold text-white">
              Trending doubts
            </h3>
          </div>

          {TRENDING.map((item, i) => {
            const count = votes[i] ?? item.votes
            return (
              <div
                key={i}
                className="glass rounded-2xl p-4 transition-colors hover:border-cyber/40"
              >
                <div className="flex gap-3">
                  <div className="flex flex-col items-center gap-1">
                    <button
                      onClick={() => toggleVote(i, item.votes)}
                      aria-label="Upvote"
                      className={cn(
                        'grid size-9 place-items-center rounded-lg border transition-colors',
                        voted[i]
                          ? 'border-cyber bg-cyber/15 text-cyber'
                          : 'border-border text-muted-foreground hover:text-white',
                      )}
                    >
                      <ArrowBigUp
                        className={cn('size-5', voted[i] && 'fill-cyber')}
                      />
                    </button>
                    <span className="text-xs font-semibold text-white">
                      {count}
                    </span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className="rounded-md border border-cyber/30 bg-cyber/10 px-2 py-0.5 text-[11px] font-medium text-cyber">
                        {item.tag}
                      </span>
                      {item.hot && (
                        <span className="flex items-center gap-1 text-[11px] font-medium text-academic">
                          <Flame className="size-3" />
                          Hot
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium leading-relaxed text-white">
                      {item.q}
                    </p>
                    <div className="mt-2.5 flex items-center gap-4 text-xs text-muted-foreground">
                      <span>@{item.author}</span>
                      <span className="flex items-center gap-1">
                        <MessageCircle className="size-3.5" />
                        {item.replies} replies
                      </span>
                      <button className="flex items-center gap-1 transition-colors hover:text-white">
                        <Share2 className="size-3.5" />
                        Share
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
              <Award className="size-4 text-academic" />
              Top toppers this week
            </div>
            <ul className="space-y-2.5">
              {LEADERBOARD.map((u, i) => (
                <li key={u.name} className="flex items-center gap-3">
                  <span
                    className={cn(
                      'grid size-7 shrink-0 place-items-center rounded-lg font-slab text-sm font-bold',
                      i === 0
                        ? 'bg-academic/20 text-academic'
                        : 'bg-secondary text-muted-foreground',
                    )}
                  >
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-white">
                      {u.name}
                    </div>
                    <div className="text-[11px] text-cyan-neon">{u.badge}</div>
                  </div>
                  <span className="text-xs font-semibold text-white">
                    {u.points.toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="glass rounded-2xl border-cyber/30 bg-gradient-to-br from-cyber/10 to-cyan-neon/5 p-4">
            <MessageSquarePlus className="mb-2 size-6 text-cyber" />
            <h4 className="font-slab text-sm font-bold text-white">
              Shape TopperGPT
            </h4>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Got a feature idea or found a bug? Your feedback trains our
              roadmap.
            </p>
            <button
              onClick={onOpenFeedback}
              className="mt-3 w-full rounded-lg bg-gradient-to-r from-cyber to-cyan-neon py-2 text-xs font-semibold text-white transition-opacity hover:opacity-90"
            >
              Share feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
