export interface Place {
  name: string
  lat: number
  lon: number
}

export interface Stop {
  id: number
  poi_id: string
  kind: string
  arrival: string
  departure: string
  locked: boolean
  order: number
}

export interface Leg {
  day_index: number
  km: number
  drive_mins: number
  geometry: [number, number][]
  stops: Stop[]
}

export interface CostItem {
  kind: string
  amount_nok: number
  is_estimate: boolean
}

export interface Variant {
  id: number
  kind: 'fastest' | 'cheapest' | 'scenic'
  total_km: number
  total_drive_mins: number
  total_cost_nok: number
  scenic_score: number
  legs: Leg[]
  cost_items: CostItem[]
}

export interface Trip {
  id: number
  name: string
  origin: Place
  destination: Place
  start_date: string
  days: number
  status: string
  chosen_variant_id: number | null
  excluded_poi_ids: string[]
  variants: Variant[]
  budget_exceeded?: Record<string, boolean>
}

export interface PoiSummary {
  id: string
  name: string
  lat: number
  lon: number
  category: string
  price_level: number
}

async function check(res: Response) {
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json()
}

export async function createTrip(input: {
  origin: Place
  destination: Place
  start_date: string
  days: number
}): Promise<Trip> {
  return check(
    await fetch('/trips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
  )
}

export async function patchStop(
  tripId: number,
  stopId: number,
  action: 'lock' | 'unlock' | 'remove',
): Promise<Trip> {
  return check(
    await fetch(`/trips/${tripId}/stops/${stopId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    }),
  )
}

export async function chooseVariant(tripId: number, variantId: number) {
  return check(
    await fetch(`/trips/${tripId}/choose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variant_id: variantId }),
    }),
  )
}

export async function fetchAllPois(): Promise<PoiSummary[]> {
  return check(await fetch('/pois/search?q='))
}
