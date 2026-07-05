import { useState } from 'react'
import { submitEvaluation, type Trip } from './api'

/** Evaluering etter reisen (DATA-01) – vises når en rute er valgt. */
export default function EvaluationBox({
  trip,
  onDone,
}: {
  trip: Trip
  onDone: () => void
}) {
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)

  if (trip.status === 'completed')
    return (
      <div className="evaluation done">
        Takk for evalueringen! Den brukes til å gjøre fremtidige forslag bedre.
      </div>
    )
  if (trip.status !== 'chosen') return null

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!rating) return
    setBusy(true)
    try {
      await submitEvaluation(trip.id, rating, text)
      onDone()
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="evaluation" onSubmit={onSubmit}>
      <h3>Hvordan var turen?</h3>
      <div className="stars" role="radiogroup" aria-label="Vurdering">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            className={n <= rating ? 'on' : ''}
            aria-label={`${n} av 5`}
            onClick={() => setRating(n)}
          >
            ★
          </button>
        ))}
      </div>
      <textarea
        value={text}
        placeholder="Hva fungerte, og hva bør vi foreslå annerledes neste gang?"
        onChange={(e) => setText(e.target.value)}
      />
      <button type="submit" disabled={busy || rating === 0}>
        Send evaluering
      </button>
    </form>
  )
}
