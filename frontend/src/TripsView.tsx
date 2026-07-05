import { useEffect, useState } from 'react'
import { getTrip, listTrips, type Trip, type TripSummary } from './api'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Utkast',
  chosen: 'Rute valgt',
  completed: 'Gjennomført',
}

export default function TripsView({ onOpen }: { onOpen: (t: Trip) => void }) {
  const [trips, setTrips] = useState<TripSummary[] | null>(null)

  useEffect(() => {
    listTrips().then(setTrips).catch(() => setTrips([]))
  }, [])

  if (trips === null) return <p>Laster …</p>
  if (trips.length === 0)
    return <p>Ingen lagrede planer ennå – lag en under «Planlegg».</p>

  return (
    <div className="trips-list">
      <h2>Mine planer</h2>
      <table>
        <thead>
          <tr>
            <th>Plan</th>
            <th>Avreise</th>
            <th>Dager</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {trips.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td>{t.start_date}</td>
              <td>{t.days}</td>
              <td>{STATUS_LABELS[t.status] ?? t.status}</td>
              <td>
                <button onClick={() => getTrip(t.id).then(onOpen)}>Åpne</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
