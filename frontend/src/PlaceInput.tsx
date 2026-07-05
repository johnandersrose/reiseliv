import { useEffect, useRef, useState } from 'react'
import { geocode, type GeocodeHit, type Place } from './api'

/** Stedssøk med forslag fra /geocode (Kartverket i produksjon, stub i dev). */
export default function PlaceInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: Place | null
  onChange: (p: Place | null) => void
}) {
  const [text, setText] = useState(value?.name ?? '')
  const [hits, setHits] = useState<GeocodeHit[]>([])
  const [open, setOpen] = useState(false)
  const timer = useRef<number>()

  useEffect(() => {
    window.clearTimeout(timer.current)
    if (text.trim().length < 2 || text === value?.name) {
      setHits([])
      return
    }
    timer.current = window.setTimeout(() => {
      geocode(text)
        .then((h) => {
          setHits(h)
          setOpen(true)
        })
        .catch(() => setHits([]))
    }, 250)
    return () => window.clearTimeout(timer.current)
  }, [text, value])

  function select(h: GeocodeHit) {
    onChange({ name: h.name, lat: h.lat, lon: h.lon })
    setText(h.name)
    setOpen(false)
  }

  return (
    <label className="place-input">
      {label}
      <input
        value={text}
        placeholder="Søk sted …"
        onChange={(e) => {
          setText(e.target.value)
          onChange(null)
        }}
        onFocus={() => hits.length && setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
      />
      {open && hits.length > 0 && (
        <ul className="suggestions">
          {hits.map((h, i) => (
            <li key={`${h.name}-${i}`}>
              <button type="button" onMouseDown={() => select(h)}>
                {h.name}
                {h.municipality && <span> · {h.municipality}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  )
}
