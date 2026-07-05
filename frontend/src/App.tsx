import { useEffect, useMemo, useState } from 'react'
import {
  chooseVariant,
  createTrip,
  fetchAllPois,
  patchStop,
  type Place,
  type Trip,
  type Variant,
} from './api'
import MapView, { VARIANT_COLORS } from './MapView'

const PRESETS: Place[] = [
  { name: 'Oslo', lat: 59.9139, lon: 10.7522 },
  { name: 'Bergen', lat: 60.3913, lon: 5.3221 },
  { name: 'Trondheim', lat: 63.4305, lon: 10.3951 },
  { name: 'Stavanger', lat: 58.969, lon: 5.7331 },
  { name: 'Kristiansand', lat: 58.1467, lon: 7.9956 },
]

const KIND_LABELS: Record<string, string> = {
  fastest: 'Raskeste',
  cheapest: 'Billigste',
  scenic: 'Vakreste',
}

const STOP_LABELS: Record<string, string> = {
  activity: 'Aktivitet',
  food: 'Mat',
  lodging: 'Overnatting',
  sight: 'Severdighet',
  rest: 'Pause',
}

function fmtTime(mins: number) {
  return `${Math.floor(mins / 60)} t ${String(mins % 60).padStart(2, '0')} min`
}

function fmtNok(n: number) {
  return `${Math.round(n).toLocaleString('nb-NO')} kr`
}

export default function App() {
  const [origin, setOrigin] = useState('Oslo')
  const [destination, setDestination] = useState('Bergen')
  const [days, setDays] = useState(3)
  const [trip, setTrip] = useState<Trip | null>(null)
  const [selected, setSelected] = useState<string>('scenic')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [poiNames, setPoiNames] = useState<Record<string, string>>({})

  useEffect(() => {
    fetchAllPois()
      .then((pois) =>
        setPoiNames(Object.fromEntries(pois.map((p) => [p.id, p.name]))),
      )
      .catch(() => {})
  }, [])

  const variant: Variant | undefined = useMemo(
    () => trip?.variants.find((v) => v.kind === selected),
    [trip, selected],
  )

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const from = PRESETS.find((p) => p.name === origin)!
      const to = PRESETS.find((p) => p.name === destination)!
      const startDate = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10)
      setTrip(await createTrip({ origin: from, destination: to, start_date: startDate, days }))
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onRemoveStop(stopId: number) {
    if (!trip) return
    setBusy(true)
    try {
      setTrip(await patchStop(trip.id, stopId, 'remove'))
    } finally {
      setBusy(false)
    }
  }

  async function onLockStop(stopId: number, locked: boolean) {
    if (!trip) return
    setTrip(await patchStop(trip.id, stopId, locked ? 'unlock' : 'lock'))
  }

  async function onChoose() {
    if (!trip || !variant) return
    await chooseVariant(trip.id, variant.id)
    setTrip({ ...trip, status: 'chosen', chosen_variant_id: variant.id })
  }

  return (
    <div className="app">
      <header>
        <h1>Reiseliv</h1>
        <p>Planlegg rundreisen – raskeste, billigste eller vakreste vei.</p>
      </header>

      <form onSubmit={onSubmit} className="trip-form">
        <label>
          Fra
          <select value={origin} onChange={(e) => setOrigin(e.target.value)}>
            {PRESETS.map((p) => (
              <option key={p.name}>{p.name}</option>
            ))}
          </select>
        </label>
        <label>
          Til
          <select value={destination} onChange={(e) => setDestination(e.target.value)}>
            {PRESETS.map((p) => (
              <option key={p.name}>{p.name}</option>
            ))}
          </select>
        </label>
        <label>
          Dager
          <input
            type="number"
            min={1}
            max={14}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          />
        </label>
        <button type="submit" disabled={busy || origin === destination}>
          {busy ? 'Genererer …' : 'Lag reiseplan'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {trip && (
        <>
          <div className="variant-cards">
            {trip.variants.map((v) => (
              <button
                key={v.kind}
                className={`card ${v.kind === selected ? 'selected' : ''}`}
                style={{ borderTopColor: VARIANT_COLORS[v.kind] }}
                onClick={() => setSelected(v.kind)}
              >
                <h2>{KIND_LABELS[v.kind]}</h2>
                <dl>
                  <div>
                    <dt>Distanse</dt>
                    <dd>{Math.round(v.total_km)} km</dd>
                  </div>
                  <div>
                    <dt>Kjøretid</dt>
                    <dd>{fmtTime(v.total_drive_mins)}</dd>
                  </div>
                  <div>
                    <dt>Estimert kostnad</dt>
                    <dd>{fmtNok(v.total_cost_nok)}</dd>
                  </div>
                  <div>
                    <dt>Naturskjønnhet</dt>
                    <dd>{'★'.repeat(Math.round(v.scenic_score * 5)).padEnd(5, '☆')}</dd>
                  </div>
                </dl>
                {trip.budget_exceeded?.[v.kind] && (
                  <p className="budget-warning">Over budsjettet ditt</p>
                )}
              </button>
            ))}
          </div>

          <MapView variants={trip.variants} selected={selected} />

          {variant && (
            <section className="day-plan">
              <div className="day-plan-header">
                <h2>Dag for dag – {KIND_LABELS[variant.kind].toLowerCase()}</h2>
                <button onClick={onChoose} disabled={trip.chosen_variant_id === variant.id}>
                  {trip.chosen_variant_id === variant.id ? 'Valgt ✓' : 'Velg denne ruten'}
                </button>
              </div>
              {variant.legs.map((leg) => (
                <article key={leg.day_index} className="day">
                  <h3>
                    Dag {leg.day_index + 1}
                    <span>
                      {Math.round(leg.km)} km · {fmtTime(leg.drive_mins)} kjøring
                    </span>
                  </h3>
                  <ul>
                    {leg.stops.map((s) => (
                      <li key={s.id}>
                        <span className="stop-time">{s.arrival}</span>
                        <span className={`stop-kind stop-${s.kind}`}>
                          {STOP_LABELS[s.kind] ?? s.kind}
                        </span>
                        <span className="stop-name">{poiNames[s.poi_id] ?? s.poi_id}</span>
                        <span className="stop-actions">
                          <button
                            title={s.locked ? 'Lås opp' : 'Lås (beholdes ved endringer)'}
                            onClick={() => onLockStop(s.id, s.locked)}
                          >
                            {s.locked ? '🔒' : '🔓'}
                          </button>
                          <button
                            title="Fjern – planen regenereres uten dette stedet"
                            onClick={() => onRemoveStop(s.id)}
                            disabled={busy}
                          >
                            ✕
                          </button>
                        </span>
                      </li>
                    ))}
                    {leg.stops.length === 0 && <li className="empty">Ren kjøredag</li>}
                  </ul>
                </article>
              ))}
              <p className="cost-note">
                Kostnader er estimater (drivstoff fra SSB-månedssnitt, sjablonger for
                overnatting/aktiviteter). Rutedata © OpenStreetMap-bidragsytere.
              </p>
            </section>
          )}
        </>
      )}
    </div>
  )
}
