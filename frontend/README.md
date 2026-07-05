# Reiseliv frontend

React + Vite + MapLibre. Viser MVP-sløyfen: skjema → tre rutevarianter
(raskeste/billigste/vakreste) → kart → dag-for-dag-plan med lås/fjern av
stopp (regenererer via backend).

## Kjør

```bash
# forutsetter backend på :8000 (cd ../backend && uvicorn app.main:app)
npm install
npm run dev        # http://localhost:5173 (proxyer /trips,/me,/pois til :8000)
npm run typecheck
npm run build
```

## Kart

Uten konfigurasjon tegnes rutene på nøytral bakgrunn (offline-vennlig — ingen
eksterne kall i dev). Sett `VITE_MAP_STYLE_URL` til en vektorflis-stil
(f.eks. MapTiler/egen tileserver) for ekte bakgrunnskart i produksjon.
OSM-attribusjon (ODbL) vises alltid.
