# Reiseliv – produktbacklog

Strukturert, deduplisert og prioritert versjon av `brukerhistorier-original.txt`
(kilde: *Brukerhistorier_kopi.docx*). Hver historie har fått en stabil ID i
opprinnelig rekkefølge per epic, slik at alt i originaldokumentet kan spores.
Duplikater er beholdt som rader, men markert **Dup** med henvisning til historien
de er slått sammen med.

## Prioriteringsmodell (MoSCoW)

| Prioritet | Betydning |
|---|---|
| **M** – Must | Inngår i MVP («tynneste hele sløyfen») |
| **S** – Should | Neste fase etter MVP |
| **C** – Could | Senere / ved kapasitet |
| **W** – Won't (nå) | Bevisst utsatt i denne omgangen (booking/betaling, tredjeparts-API-er, forretningsmodell) |
| **Dup** | Duplikat – dekkes av historien i notatfeltet |

## MVP-scope (oppsummert)

MVP er den tynneste **komplette** sløyfen:

> **Preferanser → generert ruteforslag i tre varianter («raskeste / billigste /
> vakreste») → dag-for-dag-plan med aktiviteter, overnatting og spisesteder →
> kostnadsoversikt → lagre/sammenligne planer → evaluering etter reisen.**

Bevisst **utenfor** MVP: sanntidsbooking og betaling, tredjeparts hotell-API-er,
CarPlay, chatbot, klimakompensering, gruppebetaling/purring, abonnement og
datasalg.

⚠️ **Juridisk avklaring kreves før bygging:** DATA-02 (salg av brukerdata),
BET-01–03 (kortlagring) og all posisjonslagring må GDPR-vurderes. Se egne noter.

---

## PREF – Personlige preferanser

| ID | Historie (forkortet) | Pri | Notat |
|---|---|---|---|
| PREF-01 | Registrere profil (alder, kjønn, familie) for tilpassede forslag | M | Grunnlag for hele personaliseringen |
| PREF-02 | Markere «par uten barn» → rolige/romantiske forslag | S | Reisefølge-dimensjon i profil |
| PREF-03 | Angi antall barn og alder → barnevennlige forslag | S | Reisefølge-dimensjon |
| PREF-04 | Markere reise med hund → hundevennlige steder | C | Krever POI-attributt «hundevennlig» |
| PREF-05 | Velge foretrukne aktivitetstyper, inkl. «skjulte perler» | S | Slått sammen med PREF-41 |
| PREF-06 | Filtrere forslag etter aktivitetstype (natur, kultur, sport) | M | Kjernefilter i genereringen |
| PREF-07 | Prioritere de mest populære forslagene | C | Krever popularitetsdata |
| PREF-08 | Sammenligne alternative reiseruter | M | Del av 3-varianter-flyten |
| PREF-09 | Tre versjoner uten preferanser: «raskeste», «billigste», «vakreste» | M | **MVP-ankeret** – styrer datamodellen |
| PREF-10 | Mulighet for «barnefri» reise | C | Filterattributt |
| PREF-11 | Huske tidligere preferanser og dispreferanser | S | Personaliseringsmotor – se også PREF-27/36 |
| PREF-12 | Lagre favorittreiseforslag | S | |
| PREF-13 | Sette prioriteringer mellom aktiviteter | S | |
| PREF-14 | Forslag til naturskjønne ruter | M | Realiseres som «vakreste»-varianten |
| PREF-15 | Se anmeldelser av overnatting/aktiviteter | S | Kilde: tredjepart eller egne |
| PREF-16 | Gi anmeldelser → bedre forslag neste gang | C | |
| PREF-17 | Forslag basert på tidligere bookede turer | C | Del av personaliseringsmotor |
| PREF-18 | Forslag til spisesteder langs ruten | M | POI-kategori i dagsplanen |
| PREF-19 | Aktiviteter basert på interessefelt | Dup | Dekkes av PREF-06 |
| PREF-20 | Forslag om lokale arrangementer og festivaler | C | Se også KULT-02 |
| PREF-21 | Angi maksimal tid i bil per etappe | M | Hard begrensning i rutegenerering |
| PREF-22 | Markere aktiviteter som «må oppleves» → prioriteres | S | Konfliktregel mot budsjett/rekkevidde må defineres |
| PREF-23 | Vurdere/gi tilbakemelding på reiseforslag → læring | S | |
| PREF-24 | Lagre favorittdestinasjoner → liknende forslag | C | |
| PREF-25 | Huske foretrukket overnattingstype (hotell, hytte, camping) | S | |
| PREF-26 | Foreslå hvilesteder og utsiktspunkter langs ruten | S | Slått sammen med PREF-28 |
| PREF-27 | Registrere fravalg (aktiviteter/overnatting/spisesteder) → læring | S | Personaliseringsmotor |
| PREF-28 | Naturskjønne rasteplasser | Dup | Dekkes av PREF-26 |
| PREF-29 | Velge opphold med frokost inkludert | C | |
| PREF-30 | Legge inn starttid/sluttid per dag | M | Styrer dagsplan-algoritmen |
| PREF-31 | Rangere aktiviteter → mer presise forslag | C | Overlapper PREF-13/23 |
| PREF-32 | Aktiviteter som passer både voksne og barn | Dup | Dekkes av PREF-03 |
| PREF-33 | Kortere/lengre aktiviteter etter tilgjengelig tid mellom stopp | S | Dagsplan-algoritme |
| PREF-34 | Kombinere populære og skjulte perler | C | |
| PREF-35 | Markere aktiviteter som «interessante» for senere | C | |
| PREF-36 | Huske tidligere valg ved endringer | Dup | Dekkes av PREF-11/27 |
| PREF-37 | Reisehistorikk med tilbakemeldinger og karakterer | S | Slått sammen med BRUK-14 |
| PREF-38 | Velge «temareiser» (natur, kultur, gastronomi) | S | Preset av PREF-06-filtre |
| PREF-39 | Oversikt over tjenester langs ruten (bensin, restauranter) | S | |
| PREF-40 | Rolig vs. aktiv reisestil | S | Profilattributt |
| PREF-41 | «Hemmelige perler» for reisevante | Dup | Dekkes av PREF-05 |

## INSP – Inspirasjon

| ID | Historie | Pri | Notat |
|---|---|---|---|
| INSP-01 | Reisetips og råd fra eksperter | C | Redaksjonelt innhold |
| INSP-02 | Se mest populære aktiviteter blant andre reisende | C | Krever bruksdata over tid |

## ANSV – Sosialt ansvar

| ID | Historie | Pri | Notat |
|---|---|---|---|
| ANSV-01 | Filtrere etter tilgjengelighet for funksjonshemmede | S | POI-attributt; viktig for inkludering |
| ANSV-02 | LHBT-vennlige hotell og restauranter | C | Krever pålitelig datakilde |
| ANSV-03 | Klimakompensere reisen | W | Tredjepartstjeneste; utsatt |

## KULT – Kultur

| ID | Historie | Pri | Notat |
|---|---|---|---|
| KULT-01 | Forslag til kulturelle opplevelser | S | Dekkes delvis av PREF-06 (kategori kultur) |
| KULT-02 | Opplevelser basert på regionale tradisjoner og festivaler | C | Se PREF-20 |

## VAER – Vær og sesong

| ID | Historie | Pri | Notat |
|---|---|---|---|
| VAER-01 | Forslag basert på sesong og værforhold | S | |
| VAER-02 | Integrere værmeldinger | S | MET/Yr har åpent API (verifisert i spike) |
| VAER-03 | Advare mot utendørsaktiviteter ved dårlig vær | C | |
| VAER-04 | Varsler om lokale værforhold underveis | C | Fase «under reisen» |
| VAER-05 | Se hvilke aktiviteter som er sesongbaserte | S | POI-attributt sesong |
| VAER-06 | Justere forslag ved plutselig væromslag → innendørs alternativ | C | |

## EL – Elbil

| ID | Historie | Pri | Notat |
|---|---|---|---|
| EL-01 | Rute basert på elbilens rekkevidde | S | Kjøretøy-dimensjon i profil; NOBIL-data |
| EL-02 | Legge inn ladeavtaler → prioriter «mine» ladestasjoner | C | |
| EL-03 | Forslag til pauser og ladestasjoner langs ruten | S | Slått sammen med EL-04 |
| EL-04 | Vise tilgjengelige ladestasjoner | Dup | Dekkes av EL-03 |

## OKO – Økonomi og budsjett

| ID | Historie | Pri | Notat |
|---|---|---|---|
| OKO-01 | Angi reisebudsjett → forslag innenfor ramme | M | Kjerneinput til «billigste» |
| OKO-02 | Varsler om prisendringer på bookinger | W | Krever booking (utsatt) |
| OKO-03 | Alternative ruter/tidspunkt som er billigst | S | |
| OKO-04 | Drivstoffkostnader i budsjett basert på ruten | M | Avstand × forbruk × pris |
| OKO-05 | Oversikt over fergepriser og bompenger | M | NVDB/bomdata (verifisert i spike) |
| OKO-06 | Daglig varsel om billigst diesel/bensin på ruten | C | Slått sammen med OKO-07; drivstofftype som parameter. NB: ingen åpen norsk prise-API funnet |
| OKO-07 | Daglig varsel om billigst bensin | Dup | Dekkes av OKO-06 |
| OKO-08 | Oversikt over ladepriser (elbil) | C | NOBIL har ikke sanntidspriser for alle operatører |
| OKO-09 | Samle kvitteringer i løsningen | C | |
| OKO-10 | Eksportere kvitteringer som bildefil | C | |
| OKO-11 | Integrert kostnadsoversikt per del av turen | M | |
| OKO-12 | Oversikt over rabatter og kampanjer | W | Krever partneravtaler |
| OKO-13 | Forslag basert på sesongtilbud | C | |
| OKO-14 | Estimat på totale utgifter for hele turen | M | |
| OKO-15 | Dynamisk budsjettoversikt underveis | S | Fase «under reisen» |
| OKO-16 | «Billigste»-alternativ | Dup | Dekkes av PREF-09 |
| OKO-17 | Historikk over mottatte rabatter/tilbud | W | |
| OKO-18 | Flere reisealternativer per prisklasse | S | Generalisering av PREF-09 |
| OKO-19 | Billigere alternativer for solo-reisende | C | |
| OKO-20 | Solo + sosial: fellesområder / møte andre | C | |

## BRUK – Brukervennlighet

| ID | Historie | Pri | Notat |
|---|---|---|---|
| BRUK-01 | Endre aktiviteter direkte → nye forslag genereres automatisk | M | Regenerering er kjerne-UX |
| BRUK-02 | Raskt vise overnattingsmuligheter langs ruten | S | |
| BRUK-03 | Kort introduksjon/veiledning for nye brukere | S | Onboarding |
| BRUK-04 | Oversikt over bookinger og referansenummer | W | Krever booking |
| BRUK-05 | Sanntids tilgjengelighet og pris på overnatting | W | Tredjeparts-API; utsatt |
| BRUK-06 | Integrert kalender med aktiviteter og overnatting | S | |
| BRUK-07 | Varsler om endringer i planlagte aktiviteter | C | |
| BRUK-08 | Integrasjon med Google Kalender o.l. | C | |
| BRUK-09 | Enkel registrering (Google/Apple/SoMe-innlogging) | S | |
| BRUK-10 | Automatisk alternative aktiviteter ved kansellering | C | |
| BRUK-11 | Integrere med karttjenester (ruter og avstander) | M | OSRM/OSM (verifisert i spike) |
| BRUK-12 | Tilpasse reiseplanen manuelt utover forslagene | M | |
| BRUK-13 | Endre booket reise med et par tastetrykk | Dup | Dekkes av BRUK-27 |
| BRUK-14 | «Min reisehistorikk» med tidligere turer | S | Slått sammen med PREF-37 |
| BRUK-15 | Automatisk justere forslag ved fullbooket aktivitet | C | |
| BRUK-16 | Søke på spesifikke destinasjoner | M | |
| BRUK-17 | Lagre flere reiseplaner samtidig og veksle mellom dem | M | Slått sammen med BRUK-28 |
| BRUK-18 | Web + mobil med felles brukerprofil | S | Arkitekturvalg, ikke enkeltfeature |
| BRUK-19 | Sanntids tilgjengelighet for aktiviteter | W | Krever tredjeparts-API |
| BRUK-20 | Påminnelser om bookingfrister | C | |
| BRUK-21 | Reise-sjekkliste før avreise | C | |
| BRUK-22 | Planlegge ruter med flere destinasjoner | M | Multi-stopp i rutegenerering |
| BRUK-23 | Unngå hektiske tidspunkt på rasteplasser | C | Krever besøksdata |
| BRUK-24 | Integrere tredjepartstjenester for hotellbooking | W | Utsatt (integrasjonsgjeld) |
| BRUK-25 | Personlige notater i reiseplanen | C | |
| BRUK-26 | Varsler om kanselleringer i tide | C | |
| BRUK-27 | Endre reiseplan med enkelt sveip/klikk | S | UX-prinsipp; dekker BRUK-13 |
| BRUK-28 | Lagre og hente flere planer for sammenligning | Dup | Dekkes av BRUK-17 |
| BRUK-29 | CarPlay-integrasjon | W | Utsatt |
| BRUK-30 | Automatiske påminnelser om når man bør booke | C | |

## BET – Betaling

| ID | Historie | Pri | Notat |
|---|---|---|---|
| BET-01 | Lagre betalingsmåte og valuta i innstillinger | W | ⚠️ PCI-DSS/GDPR-avklaring før bygging |
| BET-02 | Oversikt over alle betalingsmetoder | W | |
| BET-03 | Integrere betalingskort sikkert | W | Bruk betalingsleverandør (Stripe/Vipps), aldri egen kortlagring |

## SMID – Smidig reise

| ID | Historie | Pri | Notat |
|---|---|---|---|
| SMID-01 | Foreslå aktiviteter med kort ventetid | C | Krever ventetidsdata |
| SMID-02 | Reservere plass til aktiviteter på forhånd | W | Krever booking |
| SMID-03 | Forslag basert på reisetidspunkt (helg vs. ukedag) | S | |
| SMID-04 | Aktiviteter i nærheten av reiseruten | M | Korridorsøk rundt ruten |
| SMID-05 | Ta hensyn til tilgjengelig reisetid | M | |
| SMID-06 | Tilpasse forslag til turens lengde | M | |
| SMID-07 | Estimat for total reisetid | M | Fra rutemotor |
| SMID-08 | «Beste tid å reise»-anbefaling (trafikk/sesong) | C | |
| SMID-09 | Aktiviteter nær populære turistmål | S | |
| SMID-10 | Hensyn til soloppgang/solnedgang | C | |

## REIS – På reisen

| ID | Historie | Pri | Notat |
|---|---|---|---|
| REIS-01 | Push-varsler om endringer i ruteplanen | S | Fase «under reisen» |
| REIS-02 | Oversikt over parkering ved overnattingssteder | C | |
| REIS-03 | Daglig detaljert dagsplan med tidsestimater | S | Naturlig første «under reisen»-feature |

## NAV – Navigasjon

| ID | Historie | Pri | Notat |
|---|---|---|---|
| NAV-01 | Innebygd navigasjon (tid/avstand til neste stopp) | S | Vurder dyplenke til Google/Apple Maps i MVP i stedet |
| NAV-02 | Alternative ruter ved trafikk/veiarbeid | C | Slått sammen med NAV-03 |
| NAV-03 | Alternative ruter basert på sanntids trafikkdata | Dup | Dekkes av NAV-02 |
| NAV-04 | Milepæler under reisen (f.eks. kjørte km) | C | |

## VIS – Visuell fremstilling

| ID | Historie | Pri | Notat |
|---|---|---|---|
| VIS-01 | Grafisk fremstilling av reiseruten | M | Kartvisning |
| VIS-02 | Tidslinje for hele reisen | M | |
| VIS-03 | Detaljerte beskrivelser av hver aktivitet | M | |
| VIS-04 | Bilder/videoer av overnatting og aktiviteter | S | Lisensiering av bilder må avklares |
| VIS-05 | Veksle mellom visningsmoduser (liste/kart) | S | |
| VIS-06 | Nattmodus | C | |

## ABO – Abonnement

| ID | Historie | Pri | Notat |
|---|---|---|---|
| ABO-01 | Premium-funksjoner for abonnenter | W | Forretningsmodell; etter produkt-market-fit |
| ABO-02 | Månedlig vs. årlig abonnement | W | |

## KUND – Kundeservice

| ID | Historie | Pri | Notat |
|---|---|---|---|
| KUND-01 | Kontakte kundeservice via løsningen | C | |
| KUND-02 | Kontaktinfo for overnatting/aktiviteter/spisesteder | S | POI-attributt |
| KUND-03 | Chatbot som «reisehjelp» | W | Utsatt |

## DEL – Delbarhet

| ID | Historie | Pri | Notat |
|---|---|---|---|
| DEL-01 | Dele reiseplaner med familie/venner for tilbakemelding | S | Slått sammen med DEL-06 |
| DEL-02 | Eksportere reiseplan til PDF | S | Også offline-verdi (dårlig dekning i fjellet) |
| DEL-03 | Eksportere budsjett som CSV | C | |
| DEL-04 | Integrere reiseplan med sosiale medier | C | |
| DEL-05 | Integrere med reiseblogger/SoMe for andres erfaringer | C | |
| DEL-06 | Dele via e-post eller sosiale medier | Dup | Dekkes av DEL-01 |

## INNT – Inntektsstrømmer (aktør: tilbyder/forretning)

> NB: Disse historiene har en annen aktør enn sluttbrukeren og hører hjemme i
> forretningsmodellen, ikke i produktbacklogen for MVP.

| ID | Historie | Pri | Notat |
|---|---|---|---|
| INNT-01 | Promotere aktiviteter/overnatting/spisesteder | W | Annonsemodell; krever merking av promotert innhold (markedsføringsloven) |
| INNT-02 | Tilbud og rabatter direkte i reisen (abonnentfordel) | W | |
| INNT-03 | Integrerte betalingsløsninger for sømløs booking | W | |
| INNT-04 | Cashback/provisjon fra reiselivsaktører | W | |

## GRP – Gruppe

| ID | Historie | Pri | Notat |
|---|---|---|---|
| GRP-01 | Legge til reisefølge → felles preferanser i generering | C | Krever flerbruker-datamodell fra start (arkitekturnote i spec) |
| GRP-02 | Dele opp betaling og sende betalingskrav | W | Krever betaling |
| GRP-03 | Automatisk purring på gruppebetaling | W | |
| GRP-04 | Vise muligheter for gruppebooking | W | |

## DATA – Datafangst

| ID | Historie | Pri | Notat |
|---|---|---|---|
| DATA-01 | Evaluere hele reiseopplevelsen etter turen | M | Lukker MVP-læringssløyfen |
| DATA-02 | Lagre preferansedata for analyse/videresalg | W | 🚩 **GDPR-rødflagg** – krever juridisk vurdering, samtykke og trolig anonymisering. Ikke bygg uten avklaring |

---

## Statistikk

| | Antall |
|---|---|
| Historier totalt (originaldokument) | 155 |
| Duplikater slått sammen | 12 |
| **Must (MVP)** | **27** |
| Should | 44 |
| Could | 48 |
| Won't (denne fasen) | 24 |

## Kryssgående merknader

1. **Personaliseringsmotoren er ett system.** PREF-11, -12, -13, -16, -17, -22,
   -23, -24, -27, -31, -34, -35 og DATA-01 er alle input/output til samme
   preferanse- og feedbackmodell. Design den én gang (se `mvp-spec.md`).
2. **Kjøretøy er en gjennomgående dimensjon** (EL-*, OKO-04/06/08): elbil vs.
   fossil påvirker rute, budsjett og varsler. Modelleres som `Vehicle` i
   profilen fra dag én, selv om bare fossil-beregning er med i MVP.
3. **Manglende historier** (bør legges til): personvern/samtykke, autentisering
   og sikkerhet, offline-oppførsel ved dårlig dekning, ytelseskrav,
   konfliktløsning mellom motstridende preferanser.
