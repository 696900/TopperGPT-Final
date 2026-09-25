'use client'

import { SECTIONS, type SectionId } from '@/lib/sections'
import { Menu, MessageSquarePlus, Search } from 'lucide-react'

export function Topbar({
  active,
  onOpenMobile,
  onOpenFeedback,
}: {
  active: SectionId
  onOpenMobile: () => void
  onOpenFeedback: () => void
}) {
  const section = SECTIONS.find((s) => s.id === active)!

  return (
    <header className="glass sticky top-0 z-30 flex items-center gap-3 rounded-2xl px-4 py-3">
      <button
        aria-label="Open navigation"
        onClick={onOpenMobile}
        className="grid size-9 shrink-0 place-items-center rounded-lg border border-border/70 text-muted-foreground hover:text-white lg:hidden"
      >
        <Menu className="size-5" />
      </button>

      <div className="min-w-0 flex-1">
        <h1 className="flex items-center gap-2 truncate font-slab text-base font-bold text-white sm:text-lg">
          {section.label}
        </h1>
        <p className="hidden truncate text-xs text-muted-foreground sm:block">
          {section.description}
        </p>
      </div>

      <div className="hidden items-center gap-2 rounded-lg border border-border/70 bg-secondary/50 px-3 py-2 text-sm text-muted-foreground md:flex">
        <Search className="size-4" />
        <input
          className="w-40 bg-transparent outline-none placeholder:text-muted-foreground/70"
          placeholder="Search everything..."
        />
        <kbd className="rounded border border-border px-1.5 py-0.5 text-[10px]">
          /
        </kbd>
      </div>

      <button
        onClick={onOpenFeedback}
        className="hidden items-center gap-2 rounded-lg border border-border/70 px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-cyber/50 hover:text-white sm:flex"
      >
        <MessageSquarePlus className="size-4" />
        Feedback
      </button>

      <div className="flex items-center gap-2.5 rounded-full border border-border/70 bg-secondary/50 p-1 pr-3">
        <div className="grid size-7 place-items-center rounded-full bg-gradient-to-br from-cyber to-cyan-neon text-xs font-bold text-white shadow-sm">
          AS
        </div>
        <div className="hidden text-left leading-tight sm:block">
          <div className="text-xs font-medium text-white">Student</div>
          <div className="text-[10px] text-muted-foreground">Mumbai Univ.</div>
        </div>
      </div>
    </header>
  )
}
