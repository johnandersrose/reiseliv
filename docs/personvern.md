# Personvernnotat (GDPR-avklaring) – utkast til juridisk gjennomgang

> **Status:** Utkast skrevet av utviklingsteamet. Dette er *ikke* juridisk
> rådgivning — notatet strukturerer spørsmålene slik at en personvernrådgiver/
> advokat kan konkludere raskt. Må gjennomgås før første reelle bruker.

## 1. Hvilke personopplysninger behandles (MVP)

| Data | Formål | Behandlingsgrunnlag (forslag) | Lagres hvor |
|---|---|---|---|
| E-postadresse | Innlogging (magic link) | Avtale (art. 6-1 b) | Egen DB |
| Profil: alder, kjønn, reisefølge (inkl. barns alder), hund | Tilpasse reiseforslag | Avtale (art. 6-1 b) — kjernefunksjonen *er* tilpasning | Egen DB |
| Preferanser: interesser, budsjett, kjøretøy, reisestil | Tilpasse reiseforslag | Avtale (art. 6-1 b) | Egen DB |
| Reiseplaner (destinasjoner, datoer) | Levere tjenesten | Avtale (art. 6-1 b) | Egen DB |
| Evalueringer etter reise | Forbedre forslag til *samme bruker* | Avtale/berettiget interesse (art. 6-1 f) | Egen DB |

**Bevisst utenfor MVP** (reduserer risiko vesentlig):

- **Ingen betalingskortdata** (BET-01–03 er Won't). Når booking kommer: bruk
  betalingsleverandør (Vipps/Stripe) med tokenisering — kortdata skal aldri
  innom egne systemer (PCI DSS-scope holdes på leverandøren).
- **Ingen posisjonssporing.** MVP kjenner planlagt rute, ikke faktisk posisjon.
  Fase «under reisen» (REIS-*, NAV-*) endrer dette → krever ny vurdering og
  eget samtykke før den fasen bygges.
- **Ingen tredjepartsdeling** av persondata.

## 2. Punkter som krever juridisk konklusjon

1. **DATA-02 («analyser som kan selges videre») — 🚩 hovedrisikoen.**
   Videresalg av preferansedata er uforenlig med formålet dataene samles inn
   for, og krever i praksis eksplisitt, frivillig samtykke (art. 6-1 a) som må
   kunne trekkes tilbake — «ta det eller la være»-samtykke er ugyldig (art. 7-4).
   *Anbefaling:* bygg aldri DATA-02 med identifiserbare data. Hvis
   forretningsmodellen trenger det: kun **aggregert og reelt anonymisert**
   statistikk (da er GDPR ikke anvendelig), og få anonymiseringsmetoden
   vurdert — «pseudonymisert» er ikke anonymt.
2. **Barns alder i profilen (PREF-03).** Vi lagrer alder på medreisende barn
   oppgitt av forelderen. Er dette barnets personopplysning når barnet ikke er
   identifisert med navn? *Anbefaling:* lagre kun alderskategori, aldri navn
   eller fødselsdato.
3. **Profilering (art. 22).** Personaliseringen er profilering, men uten
   rettsvirkning/tilsvarende betydelig påvirkning — trolig utenfor art. 22.
   Bekreft, og beskriv profileringen i personvernerklæringen uansett.
4. **DPIA-plikt (art. 35)?** MVP: neppe (ingen sporing, ingen særlige
   kategorier i stor skala). Fase «under reisen» med posisjon: sannsynligvis ja
   — planlegg DPIA før den fasen.
5. **Utledede særlige kategorier.** LHBT-filter (ANSV-02) og
   tilgjengelighetsfilter (ANSV-01) kan *indirekte* avsløre seksuell
   orientering/helse (art. 9). *Anbefaling:* når disse bygges, lagre filteret
   som sesjonsvalg — ikke som varig profilattributt — med mindre bruker
   eksplisitt samtykker.

## 3. Tiltak som bygges inn fra start (privacy by design, art. 25)

- Samtykke-/informasjonstekst ved registrering; personvernerklæring versjoneres i repoet.
- Sletting: «slett meg» sletter bruker + preferanser + planer (kaskade i datamodellen). Evalueringer anonymiseres eller slettes.
- Dataeksport (art. 20): JSON-eksport av egne data — lav kostnad når datamodellen er ren.
- Dataminimering: `PreferenceSignal`-loggen (fase 2) får definert lagringstid (forslag: 24 mnd) fra design.
- All persondata i én database i EØS; skytjenesteleverandør med EØS-region velges.

## 4. Konklusjon (foreløpig)

MVP-en slik avgrenset i `mvp-spec.md` har **lav personvernrisiko**: vanlige
personopplysninger, klart behandlingsgrunnlag i avtalen, ingen sporing, ingen
deling. De reelle risikoene ligger i *senere* faser (DATA-02, posisjon,
betaling, ANSV-filtre) — og de er nå flagget med beslutningspunkter før
bygging. Juridisk gjennomgang av dette notatet er neste-steg nr. 1 i README.
