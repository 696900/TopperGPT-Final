export const runtime = 'nodejs'

type FeedbackPayload = {
  rating?: number
  category?: string
  message?: string
  section?: string
}

// In-memory sink for the current server lifetime. Swap this for a real
// database insert (Neon/Supabase) when persistence is required — the shape
// below is what the table should ingest.
const feedbackSink: Array<FeedbackPayload & { id: string; createdAt: string }> =
  []

export async function POST(req: Request) {
  let body: FeedbackPayload
  try {
    body = (await req.json()) as FeedbackPayload
  } catch {
    return Response.json({ ok: false, error: 'Invalid JSON' }, { status: 400 })
  }

  const rating = Number(body.rating)
  if (!rating || rating < 1 || rating > 5) {
    return Response.json(
      { ok: false, error: 'A rating between 1 and 5 is required.' },
      { status: 422 },
    )
  }
  if (!body.message || body.message.trim().length < 3) {
    return Response.json(
      { ok: false, error: 'Please add a short message.' },
      { status: 422 },
    )
  }

  const record = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    rating,
    category: body.category ?? 'general',
    message: body.message.trim().slice(0, 2000),
    section: body.section ?? 'unknown',
  }

  feedbackSink.push(record)
  console.log('[v0] feedback ingested:', record)

  return Response.json({ ok: true, id: record.id })
}

export async function GET() {
  return Response.json({ count: feedbackSink.length })
}
