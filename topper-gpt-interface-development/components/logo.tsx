import { GraduationCap, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string
  showWordmark?: boolean
}) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="relative grid size-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-cyber to-cyan-neon glow-cyber">
        <GraduationCap className="size-5 text-white" strokeWidth={2.2} />
        <Sparkles className="absolute -right-1 -top-1 size-3.5 text-academic drop-shadow" />
      </div>
      {showWordmark && (
        <div className="leading-none">
          <div className="font-slab text-[15px] font-bold tracking-tight text-white">
            Topper<span className="text-cyber">GPT</span>
          </div>
          <div className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Intelligence
          </div>
        </div>
      )}
    </div>
  )
}
