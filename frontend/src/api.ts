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

export interface GeocodeHit {
  name: string
  lat: number
  lon: number
  municipality: string
}

export interface Preferences {
  party_adults: number
  party_children_ages: number[]
  dog: boolean
  vehicle: { type: string; consumption_per_100km?: number | null }
  interests: string[]
  budget_total_nok: number | null
  max_drive_mins_per_leg: number
  day_start: string
  day_end: string
  lodging_types: string[]
}

export interface TripSummary {
  id: number
  name: string
  status: string
  days: number
  start_date: string
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('reiseliv_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function check(res: Response) {
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json()
}

async function get(url: string) {
  return check(await fetch(url, { headers: authHeaders() }))
}

async function send(url: string, method: string, body?: unknown) {
  return check(
    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  )
}

export async function createTrip(input: {
  origin: Place
  destination: Place
  start_date: string
  days: number
}): Promise<Trip> {
  return send('/trips', 'POST', input)
}

export async function patchStop(
  tripId: number,
  stopId: number,
  action: 'lock' | 'unlock' | 'remove',
): Promise<Trip> {
  return send(`/trips/${tripId}/stops/${stopId}`, 'PATCH', { action })
}

export async function chooseVariant(tripId: number, variantId: number) {
  return send(`/trips/${tripId}/choose`, 'POST', { variant_id: variantId })
}

export async function fetchAllPois(): Promise<PoiSummary[]> {
  return get('/pois/search?q=')
}

export async function geocode(q: string): Promise<GeocodeHit[]> {
  return get(`/geocode?q=${encodeURIComponent(q)}`)
}

export async function listTrips(): Promise<TripSummary[]> {
  return get('/trips')
}

export async function getTrip(id: number): Promise<Trip> {
  return get(`/trips/${id}`)
}

export async function getPreferences(): Promise<Preferences> {
  return get('/me/preferences')
}

export async function putPreferences(p: Preferences): Promise<Preferences> {
  return send('/me/preferences', 'PUT', p)
}

export async function submitEvaluation(tripId: number, rating: number, text: string) {
  return send(`/trips/${tripId}/evaluation`, 'POST', { rating, text })
}

export async function requestLoginLink(
  email: string,
): Promise<{ sent: boolean; dev_link?: string }> {
  return send('/auth/request-link', 'POST', { email })
}

export async function verifyLogin(token: string): Promise<{ token: string; email: string }> {
  return send('/auth/verify', 'POST', { token })
}
