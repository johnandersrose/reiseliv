#!/usr/bin/env python3
"""Datafeasibility-spike for Reiseliv: Oslo → Bergen.

Tester om vi kan hente ekte data for de tre rutevariantene
(«raskeste / billigste / vakreste») fra åpne kilder:

  1. Ruting med alternativer      – OSRM demo-server (kun til spike!)
  2. Bomstasjoner                 – NVDB API Les (Statens vegvesen, NLOD)
  3. Drivstoffpris (månedssnitt)  – SSB tabell 09654
  4. Værvarsel langs ruten        – MET Norway locationforecast 2.0
  5. Utsiktspunkter (scenic-POI)  – OpenStreetMap Overpass

Kjøres lokalt (krever fri internettilgang – sandkasser med proxy-policy
blokkerer gjerne disse hostene):

    python3 spike/oslo_bergen_spike.py

Kun standardbibliotek – ingen avhengigheter.
"""
import json
import sys
import urllib.parse
import urllib.request

UA = "reiseliv-spike/0.1 (kontakt: john.anders.rose@gmail.com)"
OSLO = (10.7522, 59.9139)   # lon, lat
BERGEN = (5.3221, 60.3913)

FUEL_L_PER_100KM = 6.5      # antatt forbruk, fossilbil


def fetch(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def step(title):
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


def try_step(title, fn):
    step(title)
    try:
        return fn()
    except Exception as e:  # spike: vis feilen, fortsett
        print(f"  FEIL: {type(e).__name__}: {e}")
        return None


def route_osrm():
    url = ("https://router.project-osrm.org/route/v1/driving/"
           f"{OSLO[0]},{OSLO[1]};{BERGEN[0]},{BERGEN[1]}"
           "?alternatives=true&overview=false")
    data = fetch(url)
    routes = data.get("routes", [])
    print(f"  {len(routes)} rutealternativ(er):")
    for i, r in enumerate(routes):
        print(f"    #{i}: {r['distance']/1000:.0f} km, {r['duration']/3600:.1f} t")
    return routes


def toll_stations_nvdb():
    # Objekttype 45 = Bomstasjon. V4-dok: https://nvdb-docs.atlas.vegvesen.no
    for base in ("https://nvdbapiles.atlas.vegvesen.no",
                 "https://nvdbapiles-v3.atlas.vegvesen.no"):
        try:
            data = fetch(f"{base}/vegobjekter/45?antall=5&inkluder=egenskaper",
                         headers={"Accept": "application/vnd.vegvesen.nvdb-v3-rev1+json",
                                  "X-Client": UA})
            objs = data.get("objekter", [])
            print(f"  {base}: {len(objs)} bomstasjoner (av totalt "
                  f"{data.get('metadata', {}).get('antall', '?')} i første side)")
            for o in objs[:3]:
                navn = next((e.get("verdi") for e in o.get("egenskaper", [])
                             if e.get("navn") == "Navn bomstasjon"), "?")
                takst = next((e.get("verdi") for e in o.get("egenskaper", [])
                              if "takst" in e.get("navn", "").lower()), "?")
                print(f"    id={o['id']}  navn={navn}  takst={takst}")
            return objs
        except Exception as e:
            print(f"  {base}: {type(e).__name__}: {e}")
    return None


def fuel_price_ssb():
    # SSB 09654: Priser på drivstoff (kr/liter), månedlig. Åpent API.
    query = {
        "query": [
            {"code": "PetroleumProd", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "top", "values": ["1"]}},
        ],
        "response": {"format": "json-stat2"},
    }
    data = fetch("https://data.ssb.no/api/v0/no/table/09654",
                 data=json.dumps(query).encode(),
                 headers={"Content-Type": "application/json"})
    labels = list(data["dimension"]["PetroleumProd"]["category"]["label"].values())
    month = list(data["dimension"]["Tid"]["category"]["label"].values())[0]
    prices = dict(zip(labels, data["value"]))
    print(f"  Månedssnitt {month}:")
    for k, v in prices.items():
        print(f"    {k}: {v} kr/l")
    return prices


def weather_met():
    lon, lat = 7.10, 60.40  # midt på Hardangervidda
    data = fetch(f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
                 f"?lat={lat}&lon={lon}")
    first = data["properties"]["timeseries"][0]
    t = first["data"]["instant"]["details"]["air_temperature"]
    print(f"  Hardangervidda {first['time']}: {t} °C")
    return data


def viewpoints_overpass():
    # Utsiktspunkter i en boks over Hardangervidda → input til scenicScore
    q = '[out:json][timeout:25];node["tourism"="viewpoint"](59.9,6.5,60.6,7.6);out count;'
    data = fetch("https://overpass-api.de/api/interpreter",
                 data=urllib.parse.urlencode({"data": q}).encode())
    n = data["elements"][0]["tags"]["nodes"] if data.get("elements") else "?"
    print(f"  tourism=viewpoint i Hardangervidda-boksen: {n}")
    return n


def main():
    routes = try_step("1. Ruting Oslo→Bergen (OSRM demo)", route_osrm)
    try_step("2. Bomstasjoner (NVDB objekttype 45)", toll_stations_nvdb)
    prices = try_step("3. Drivstoffpriser (SSB 09654)", fuel_price_ssb)
    try_step("4. Værvarsel (MET locationforecast)", weather_met)
    try_step("5. Utsiktspunkter (OSM Overpass)", viewpoints_overpass)

    if routes and prices:
        step("Estimat: drivstoffkost «raskeste» variant")
        km = routes[0]["distance"] / 1000
        petrol = next((v for k, v in prices.items() if "ensin" in k), None)
        if petrol:
            cost = km / 100 * FUEL_L_PER_100KM * petrol
            print(f"  {km:.0f} km × {FUEL_L_PER_100KM} l/100km × {petrol} kr/l "
                  f"≈ {cost:.0f} kr")
    print("\nFerdig. Se RESULTS.md for tolkning.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
