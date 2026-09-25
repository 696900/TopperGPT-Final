'use client'

import { useState } from 'react'
import { type SectionId } from '@/lib/sections'
import { Sidebar } from '@/components/sidebar'
import { Topbar } from '@/components/topbar'
import { FeedbackDrawer } from '@/components/feedback-drawer'
import { AiTutor } from '@/components/modules/ai-tutor'
import { PredictedPapers } from '@/components/modules/predicted-papers'
import { SmartNotes } from '@/components/modules/smart-notes'
import { ResearchHub } from '@/components/modules/research-hub'
import { CommunityInsights } from '@/components/modules/community-insights'

export function AppShell() {
  const [active, setActive] = useState<SectionId>('tutor')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)

  return (
    <div className="cyber-grid min-h-svh">
      <div className="flex min-h-svh gap-0 p-2 sm:p-3 lg:gap-3 lg:p-3">
        <Sidebar
          active={active}
          onSelect={setActive}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((c) => !c)}
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <Topbar
            active={active}
            onOpenMobile={() => setMobileOpen(true)}
            onOpenFeedback={() => setFeedbackOpen(true)}
          />

          <main className="min-h-0 flex-1">
            {active === 'tutor' && <AiTutor />}
            {active === 'papers' && <PredictedPapers />}
            {active === 'notes' && <SmartNotes />}
            {active === 'research' && <ResearchHub />}
            {active === 'community' && (
              <CommunityInsights onOpenFeedback={() => setFeedbackOpen(true)} />
            )}
          </main>
        </div>
      </div>

      <FeedbackDrawer
        open={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        section={active}
      />
    </div>
  )
}
