#!/usr/bin/env bash
# Engangsoppsett for lokal infrastruktur: laster Geofabrik Norge-ekstrakt
# (~1,2 GB) og starter Valhalla (bygger tiles første gang, tar 20–40 min)
# + PostGIS. Krever docker compose og fri internettilgang.
set -euo pipefail
cd "$(dirname "$0")"

PBF=valhalla_data/norway-latest.osm.pbf
mkdir -p valhalla_data

if [ ! -f "$PBF" ]; then
  echo "Laster ned Norge-ekstrakt fra Geofabrik (~1,2 GB)..."
  curl -L --fail -o "$PBF" \
    https://download.geofabrik.de/europe/norway-latest.osm.pbf
else
  echo "Norge-ekstrakt finnes allerede: $PBF"
fi

echo "Starter Valhalla + PostGIS..."
docker compose up -d

echo
echo "Valhalla bygger tiles i bakgrunnen (første gang: 20–40 min)."
echo "Følg med:   docker compose logs -f valhalla"
echo "Test når klar:"
echo '  curl -s localhost:8002/route -d '"'"'{"locations":[{"lat":59.9139,"lon":10.7522},{"lat":60.3913,"lon":5.3221}],"costing":"auto"}'"'"' | head -c 300'
echo
echo "Backend mot ekte rutemotor:"
echo "  cd ../backend && ROUTING_PROVIDER=valhalla uvicorn app.main:app"
