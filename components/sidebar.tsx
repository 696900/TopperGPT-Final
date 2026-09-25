'use client'

import { SECTIONS, type SectionId } from '@/lib/sections'
import { Logo } from '@/components/logo'
import { cn } from '@/lib/utils'
import { ChevronLeft, PanelLeftOpen, X } from 'lucide-react'

const ACCENT_CLASS: Record<string, string> = {
  cyber: 'text-cyber',
  'cyan-neon': 'text-cyan-neon',
  academic: 'text-academic',
}

export function Sidebar({
  active,
  onSelect,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
}: {
  active: SectionId
  onSelect: (id: SectionId) => void
  collapsed: boolean
  onToggleCollapse: () => void
  mobileOpen: boolean
  onCloseMobile: () => void
}) {
  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col gap-4 p-3 transition-[width,transform] duration-300 ease-out lg:relative lg:z-auto lg:translate-x-0',
          collapsed ? 'lg:w-[76px]' : 'lg:w-[268px]',
          'w-[268px]',
          mobileOpen ? 'translate-x-0' : '-translate-x-[110%]',
        )}
      >
        <nav className="glass flex h-full flex-col rounded-2xl p-3">
          {/* Header */}
          <div className="flex items-center justify-between px-1 pb-3">
            {collapsed ? (
              <Logo showWordmark={false} className="mx-auto" />
            ) : (
              <Logo />
            )}
            <button
              aria-label="Close navigation"
              onClick={onCloseMobile}
              className="grid size-8 place-items-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-white lg:hidden"
            >
              <X className="size-4" />
            </button>
          </div>

          <div className="mx-1 mb-3 h-px bg-border/70" />

          {/* Nav items */}
          <ul className="flex flex-1 flex-col gap-1.5">
            {SECTIONS.map((s) => {
              const isActive = active === s.id
              const Icon = s.icon
              return (
                <li key={s.id}>
                  <button
                    onClick={() => {
                      onSelect(s.id)
                      onCloseMobile()
                    }}
                    title={collapsed ? s.label : undefined}
                    className={cn(
                      'group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors',
                      collapsed && 'lg:justify-center lg:px-0',
                      isActive
                        ? 'bg-secondary text-white'
                        : 'text-muted-foreground hover:bg-secondary/60 hover:text-white',
                    )}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-cyber to-cyan-neon" />
                    )}
                    <Icon
                      className={cn(
                        'size-5 shrink-0 transition-colors',
                        isActive
                          ? ACCENT_CLASS[s.accent]
                          : 'text-muted-foreground group-hover:text-white',
                      )}
                    />
                    {!collapsed && (
                      <span className="flex min-w-0 flex-col">
                        <span className="truncate text-sm font-medium">
                          {s.label}
                        </span>
                        <span className="truncate text-[11px] text-muted-foreground">
                          {s.short}
                        </span>
                      </span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>

          {/* Collapse toggle (desktop) */}
          <button
            onClick={onToggleCollapse}
            className="mt-3 hidden items-center justify-center gap-2 rounded-lg border border-border/70 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-white lg:flex"
          >
            {collapsed ? (
              <PanelLeftOpen className="size-4" />
            ) : (
              <>
                <ChevronLeft className="size-4" />
                Collapse
              </>
            )}
          </button>
        </nav>
      </aside>
    </>
  )
}
