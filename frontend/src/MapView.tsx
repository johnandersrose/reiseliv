import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef } from 'react'
import type { Variant } from './api'

// Uten ekstern flis-URL rendres kun rutelinjene på nøytral bakgrunn (offline-
// vennlig i dev). Sett VITE_MAP_STYLE_URL til en vektorflis-stil i produksjon.
const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#e8ecef' } }],
}

export const VARIANT_COLORS: Record<string, string> = {
  fastest: '#3466c0',
  cheapest: '#2e8b57',
  scenic: '#c05a34',
}

export default function MapView({
  variants,
  selected,
}: {
  variants: Variant[]
  selected: string
}) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)

  useEffect(() => {
    if (!container.current) return
    const styleUrl = import.meta.env.VITE_MAP_STYLE_URL as string | undefined
    map.current = new maplibregl.Map({
      container: container.current,
      style: styleUrl || STYLE,
      center: [8, 60.2],
      zoom: 5.5,
      attributionControl: false,
    })
    map.current.addControl(
      new maplibregl.AttributionControl({
        customAttribution: 'Rutedata © OpenStreetMap-bidragsytere (ODbL)',
      }),
    )
    return () => map.current?.remove()
  }, [])

  useEffect(() => {
    const m = map.current
    if (!m || variants.length === 0) return

    const draw = () => {
      const bounds = new maplibregl.LngLatBounds()
      for (const v of variants) {
        const coords = v.legs.flatMap((l) => l.geometry)
        coords.forEach((c) => bounds.extend(c))
        const id = `route-${v.kind}`
        const data: GeoJSON.Feature = {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords },
        }
        const existing = m.getSource(id) as maplibregl.GeoJSONSource | undefined
        if (existing) {
          existing.setData(data)
        } else {
          m.addSource(id, { type: 'geojson', data })
          m.addLayer({
            id,
            type: 'line',
            source: id,
            paint: { 'line-color': VARIANT_COLORS[v.kind], 'line-width': 3 },
          })
        }
        m.setPaintProperty(id, 'line-width', v.kind === selected ? 6 : 3)
        m.setPaintProperty(id, 'line-opacity', v.kind === selected ? 1 : 0.45)
      }
      if (!bounds.isEmpty()) m.fitBounds(bounds, { padding: 48, duration: 400 })
    }

    if (m.isStyleLoaded()) draw()
    else m.once('load', draw)
  }, [variants, selected])

  return <div ref={container} className="map" />
}
