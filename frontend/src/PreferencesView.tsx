import { useEffect, useState } from 'react'
import { getPreferences, putPreferences, type Preferences } from './api'

const INTERESTS = ['natur', 'kultur', 'sport', 'gastronomi', 'familie']
const VEHICLES = [
  { value: 'petrol', label: 'Bensin' },
  { value: 'diesel', label: 'Diesel' },
  { value: 'ev', label: 'Elbil' },
]

export default function PreferencesView() {
  const [prefs, setPrefs] = useState<Preferences | null>(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getPreferences().then(setPrefs).catch(() => {})
  }, [])

  if (!prefs) return <p>Laster …</p>

  function set<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    setPrefs({ ...prefs!, [key]: value })
    setSaved(false)
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      setPrefs(await putPreferences(prefs!))
      setSaved(true)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="prefs" onSubmit={onSave}>
      <h2>Mine preferanser</h2>
      <p className="hint">
        Brukes når reiseplaner genereres: interesser filtrerer aktiviteter,
        budsjettet flagger for dyre varianter, og kjøretiden per dag er en hard
        grense.
      </p>

      <fieldset>
        <legend>Reisefølge</legend>
        <label>
          Voksne
          <input
            type="number"
            min={1}
            max={9}
            value={prefs.party_adults}
            onChange={(e) => set('party_adults', Number(e.target.value))}
          />
        </label>
        <label>
          Barnas aldre (kommaseparert)
          <input
            value={prefs.party_children_ages.join(', ')}
            placeholder="f.eks. 4, 9"
            onChange={(e) =>
              set(
                'party_children_ages',
                e.target.value
                  .split(',')
                  .map((s) => Number(s.trim()))
                  .filter((n) => Number.isFinite(n) && n > 0),
              )
            }
          />
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={prefs.dog}
            onChange={(e) => set('dog', e.target.checked)}
          />
          Reiser med hund
        </label>
      </fieldset>

      <fieldset>
        <legend>Kjøretøy</legend>
        <label>
          Type
          <select
            value={prefs.vehicle.type}
            onChange={(e) => set('vehicle', { ...prefs.vehicle, type: e.target.value })}
          >
            {VEHICLES.map((v) => (
              <option key={v.value} value={v.value}>
                {v.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Forbruk ({prefs.vehicle.type === 'ev' ? 'kWh' : 'liter'}/100 km)
          <input
            type="number"
            step="0.1"
            min={0}
            value={prefs.vehicle.consumption_per_100km ?? ''}
            placeholder={prefs.vehicle.type === 'ev' ? '18' : '6.5'}
            onChange={(e) =>
              set('vehicle', {
                ...prefs.vehicle,
                consumption_per_100km: e.target.value ? Number(e.target.value) : null,
              })
            }
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Interesser</legend>
        <div className="interest-row">
          {INTERESTS.map((i) => (
            <label key={i} className="checkbox">
              <input
                type="checkbox"
                checked={prefs.interests.includes(i)}
                onChange={(e) =>
                  set(
                    'interests',
                    e.target.checked
                      ? [...prefs.interests, i]
                      : prefs.interests.filter((x) => x !== i),
                  )
                }
              />
              {i}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend>Rammer</legend>
        <label>
          Totalbudsjett (kr, valgfritt)
          <input
            type="number"
            min={0}
            value={prefs.budget_total_nok ?? ''}
            placeholder="f.eks. 15000"
            onChange={(e) =>
              set('budget_total_nok', e.target.value ? Number(e.target.value) : null)
            }
          />
        </label>
        <label>
          Maks kjøretid per dag (minutter)
          <input
            type="number"
            min={60}
            max={720}
            step={30}
            value={prefs.max_drive_mins_per_leg}
            onChange={(e) => set('max_drive_mins_per_leg', Number(e.target.value))}
          />
        </label>
        <label>
          Dagen starter
          <input
            type="time"
            value={prefs.day_start}
            onChange={(e) => set('day_start', e.target.value)}
          />
        </label>
        <label>
          Dagen slutter
          <input
            type="time"
            value={prefs.day_end}
            onChange={(e) => set('day_end', e.target.value)}
          />
        </label>
      </fieldset>

      <div className="prefs-actions">
        <button type="submit" disabled={busy}>
          {busy ? 'Lagrer …' : 'Lagre preferanser'}
        </button>
        {saved && <span className="saved">Lagret ✓</span>}
      </div>
    </form>
  )
}
