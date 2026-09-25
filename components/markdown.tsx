'use client'

import { memo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Check, Copy } from 'lucide-react'

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="group relative">
      <button
        onClick={() => {
          navigator.clipboard.writeText(code)
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        }}
        className="absolute right-2 top-2 z-10 flex items-center gap-1 rounded-md border border-border bg-secondary/80 px-2 py-1 text-[11px] text-muted-foreground opacity-0 transition-opacity hover:text-white group-hover:opacity-100"
        aria-label="Copy code"
      >
        {copied ? (
          <>
            <Check className="size-3 text-chart-5" /> Copied
          </>
        ) : (
          <>
            <Copy className="size-3" /> Copy
          </>
        )}
      </button>
    </div>
  )
}

export const Markdown = memo(function Markdown({
  content,
}: {
  content: string
}) {
  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre({ children }) {
            const codeText = extractText(children)
            return (
              <div className="relative">
                <CodeBlock code={codeText} />
                <pre>{children}</pre>
              </div>
            )
          },
          a({ children, ...props }) {
            return (
              <a {...props} target="_blank" rel="noreferrer">
                {children}
              </a>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
})

function extractText(node: unknown): string {
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (node && typeof node === 'object' && 'props' in node) {
    // @ts-expect-error runtime access of react element children
    return extractText(node.props?.children)
  }
  return ''
}
