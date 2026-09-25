import { generateText } from 'ai'

export const maxDuration = 30

const PROMPTS = {
  notes: (input: string) =>
    `You are TopperGPT's Smart Notes Synthesizer. Convert the following study material into concise, exam-ready notes.

Return clean Markdown with this structure:
## TL;DR
(2-3 sentence overview)
## Key Concepts
(bulleted definitions of the most important terms)
## Detailed Summary
(structured bullets grouped under bold sub-topics)
## Formulas / Key Facts
(a Markdown table when relevant, else bullets)
## Likely Exam Questions
(3-5 probable questions based on the material)

Source material:
"""
${input}
"""`,
  research: (input: string) =>
    `You are TopperGPT's Topic Research Hub. Build a rigorous learning guide for the topic below, aimed at an engineering undergraduate.

Return clean Markdown with this structure:
## Overview
## Prerequisites
(bulleted)
## Core Concepts
(numbered, each with a one-line explanation)
## Step-by-Step Learning Path
(ordered milestones from beginner to advanced)
## Common Pitfalls
## Practice & Application
(concrete problems or projects to try)

Topic:
"""
${input}
"""`,
} as const

export async function POST(req: Request) {
  let mode: keyof typeof PROMPTS
  let input: string
  try {
    const body = (await req.json()) as { mode?: string; input?: string }
    mode = (body.mode as keyof typeof PROMPTS) ?? 'notes'
    input = body.input ?? ''
  } catch {
    return Response.json({ error: 'Invalid request' }, { status: 400 })
  }

  if (!PROMPTS[mode]) {
    return Response.json({ error: 'Unknown mode' }, { status: 400 })
  }
  if (input.trim().length < 10) {
    return Response.json(
      { error: 'Please provide more content to work with.' },
      { status: 422 },
    )
  }

  try {
    const { text } = await generateText({
      model: 'openai/gpt-5-mini',
      prompt: PROMPTS[mode](input.slice(0, 12000)),
    })
    return Response.json({ text })
  } catch (e) {
    console.log('[v0] generate error:', e)
    return Response.json(
      { error: 'Generation failed. Please try again.' },
      { status: 500 },
    )
  }
}
