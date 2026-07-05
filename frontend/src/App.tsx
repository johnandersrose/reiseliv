import { useEffect, useMemo, useState } from 'react'
import {
  chooseVariant,
  createTrip,
  fetchAllPois,
  getTrip,
  patchStop,
  requestLoginLink,
  verifyLogin,
  type Place,
  type Trip,
  type Variant,
} from './api'
import EvaluationBox from './EvaluationBox'
import MapView, { VARIANT_COLORS } from './MapView'
import PlaceInput from './PlaceInput'
import PreferencesView from './PreferencesView'
import TripsView from './TripsView'

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

type View = 'plan' | 'trips' | 'prefs'

function fmtTime(mins: number) {
  return `${Math.floor(mins / 60)} t ${String(mins % 60).padStart(2, '0')} min`
}

function fmtNok(n: number) {
  return `${Math.round(n).toLocaleString('nb-NO')} kr`
}

export default function App() {
  const [view, setView] = useState<View>('plan')
  const [origin, setOrigin] = useState<Place | null>(null)
  const [destination, setDestination] = useState<Place | null>(null)
  const [days, setDays] = useState(3)
  const [startDate, setStartDate] = useState(
    () => new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10),
  )
  const [trip, setTrip] = useState<Trip | null>(null)
  const [selected, setSelected] = useState<string>('scenic')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [poiNames, setPoiNames] = useState<Record<string, string>>({})
  const [email, setEmail] = useState(() => localStorage.getItem('reiseliv_email'))
  const [loginEmail, setLoginEmail] = useState('')
  const [loginMsg, setLoginMsg] = useState('')

  useEffect(() => {
    fetchAllPois()
      .then((pois) => setPoiNames(Object.fromEntries(pois.map((p) => [p.id, p.name]))))
      .catch(() => {})
    // Magic link: ?login_token=… i URL-en fullfører innloggingen.
    const params = new URLSearchParams(window.location.search)
    const token = params.get('login_token')
    if (token) {
      verifyLogin(token)
        .then((r) => {
          localStorage.setItem('reiseliv_token', r.token)
          localStorage.setItem('reiseliv_email', r.email)
          setEmail(r.email)
        })
        .catch(() => setLoginMsg('Innloggingslenken er ugyldig eller utløpt.'))
        .finally(() => window.history.replaceState({}, '', window.location.pathname))
    }
  }, [])

  const variant: Variant | undefined = useMemo(
    () => trip?.variants.find((v) => v.kind === selected),
    [trip, selected],
  )

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!origin || !destination) return
    setBusy(true)
    setError('')
    try {
      setTrip(await createTrip({ origin, destination, start_date: startDate, days }))
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

  async function onLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoginMsg('')
    const r = await requestLoginLink(loginEmail)
    if (r.dev_link) {
      // Dev-modus: følg lenken direkte i stedet for å vente på e-post.
      const token = new URL(r.dev_link).searchParams.get('login_token')!
      const v = await verifyLogin(token)
      localStorage.setItem('reiseliv_token', v.token)
      localStorage.setItem('reiseliv_email', v.email)
      setEmail(v.email)
      setTrip(null)
    } else {
      setLoginMsg('Sjekk e-posten din for innloggingslenken.')
    }
  }

  function onLogout() {
    localStorage.removeItem('reiseliv_token')
    localStorage.removeItem('reiseliv_email')
    setEmail(null)
    setTrip(null)
  }

  return (
    <div className="app">
      <header>
        <div className="header-row">
          <h1>Reiseliv</h1>
          {email ? (
            <div className="auth">
              <span>{email}</span>
              <button onClick={onLogout}>Logg ut</button>
            </div>
          ) : (
            <form className="auth" onSubmit={onLogin}>
              <input
                type="email"
                required
                placeholder="din@epost.no"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
              />
              <button type="submit">Logg inn</button>
            </form>
          )}
        </div>
        <p>Planlegg rundreisen – raskeste, billigste eller vakreste vei.</p>
        {loginMsg && <p className="hint">{loginMsg}</p>}
        <nav className="tabs">
          {(
            [
              ['plan', 'Planlegg'],
              ['trips', 'Mine planer'],
              ['prefs', 'Preferanser'],
            ] as [View, string][]
          ).map(([v, label]) => (
            <button
              key={v}
              className={view === v ? 'active' : ''}
              onClick={() => setView(v)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      {view === 'prefs' && <PreferencesView />}
      {view === 'trips' && (
        <TripsView
          onOpen={(t) => {
            setTrip(t)
            setView('plan')
          }}
        />
      )}

      {view === 'plan' && (
        <>
          <form onSubmit={onSubmit} className="trip-form">
            <PlaceInput label="Fra" value={origin} onChange={setOrigin} />
            <PlaceInput label="Til" value={destination} onChange={setDestination} />
            <label>
              Avreise
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
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
            <button type="submit" disabled={busy || !origin || !destination}>
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
                    <button
                      onClick={onChoose}
                      disabled={trip.chosen_variant_id === variant.id}
                    >
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
                            <span className="stop-name">
                              {poiNames[s.poi_id] ?? s.poi_id}
                            </span>
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
                  <EvaluationBox
                    trip={trip}
                    onDone={() => getTrip(trip.id).then(setTrip)}
                  />
                  <p className="cost-note">
                    Kostnader er estimater (drivstoff fra SSB-månedssnitt, sjablonger for
                    overnatting/aktiviteter). Rutedata © OpenStreetMap-bidragsytere.
                  </p>
                </section>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
