# Parameter sources for the nine-city calibration

Retrieval date for every row: **2026-10-23** (all web pages fetched or searched on that day; FX and fuel prices as of the dates shown in the rows). Machine-readable versions: `city_parameters.csv` (long format, 361 rows, with per-row source, URL, quality flag and note) and `city_parameters_wide.csv` (one recommended calibration row per city). London, Paris and Berlin were added on 2026-10-23 with the same schema, parameter names and flags (rows 239 onward in the CSV, references [79] onward); the six original cities are unchanged.

City keys: the repository folder `Bombay` is Mumbai. GHSL populations come from `data/processed/<city>/meta.json` (GHS-POP R2023A, epoch 2025).

## Quality flags

- **A**: official or primary statistic for that city (government statistic, company filing, or a city-specific measurement such as the TomTom Traffic Index city page).
- **B**: reputable industry report, secondary reproduction of an official figure, or a country-level proxy.
- **C**: rough estimate, derived number with an assumption, proxy from another place, or secondary web source.

## Recommended calibration (wide table)

| city | parcels/cap/day | TomTom cong. % | min/10 km | drops/veh/day | shift h | van cap. | fee USD | wage USD/h | fuel USD/L | N carriers | pop. (M) | veh/1000 | lane cap. veh/h | BPR a | BPR b |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| New Delhi | 0.00964 | 60.2 | 24.0 | 40 | 10 | 40 | 0.69 | 1.07 | 1.15 | 5 | 30.2 | 400 | 1000 | 0.15 | 4 |
| Cairo | 0.00561 | 40.5 | 22.38 | 40 | 8.4 | 40 | 1.18 | 0.61 | 0.44 | 4 | 25.6 | 220 | 1000 | 0.15 | 4 |
| Moscow | 0.15572 | 54 | 25.0 | 70 | 8.4 | 126 | 3.67 | 4.53 | 0.9 | 5 | 13.274 | 297 | 1000 | 0.15 | 4 |
| Buenos Aires | 0.01505 | 48.1 | 31.58 | 70 | 8.4 | 126 | 0.98 | 1.28 | 1.45 | 4 | 13.986 | 331 | 1000 | 0.15 | 4 |
| New York | 0.18356 | 48.8 | 31.58 | 120 | 8.4 | 226 | 9.09 | 22.27 | 1.22 | 4 | 20.112 | 242 | 1000 | 0.15 | 4 |
| Mumbai | 0.00964 | 63.2 | 28.85 | 40 | 10 | 40 | 0.69 | 1.07 | 1.15 | 5 | 20.2 | 330 | 1000 | 0.15 | 4 |
| London | 0.16609 | 51.6 | 36.36 | 72 | 7.3 | 126 | 4.21 | 18.76 | 2.34 | 5 | 9.123 | 288 | 1000 | 0.15 | 4 |
| Paris | 0.06496 | 40.0 | 30.0 | 70 | 8.4 | 126 | 6.04 | 15.72 | 2.42 | 5 | 12.463 | 575 | 1000 | 0.15 | 4 |
| Berlin | 0.14338 | 44.6 | 28.99 | 126 | 8.4 | 206 | 4.40 | 18.78 | 2.39 | 6 | 3.914 | 330 | 1000 | 0.15 | 4 |

Notes on the wide table: parcels per capita per day are **country-level** (India national e-commerce shipments for both Indian cities; Egypt, Russia, Argentina, US national figures). The TomTom figures are the 'City' tab for 2025. Moscow is absent from the 2025 TomTom index: its congestion value is TomTom 2020 and its minutes per 10 km are derived from a 24 km/h peak speed (peak only). Fuel is Octane-95 gasoline; diesel is in the long table. Population is the official figure in `population_official_millions` (definitions differ by city, see the next section).

Notes on the three European rows (added 2026-10-23): parcels per capita per day are again **country-level** (UK Ofcom 4.2bn parcels FY2024-25 over 69.28M people; France ARCEP 1,638M parcels delivered in 2024 over 69.08M; Germany BPEX 4.37bn KEP shipments in 2025 over 83.5M) and include B2B, so they overstate pure B2C (Germany: about 60% B2C). TomTom values are the 2025 'City' tab; the 'Metro' tab values are in the notes of the CSV rows. Minutes per 10 km are 600 / all-day average speed, as for the other cities. Fuel is gasoline (USD/L, GlobalPetrolPrices 19 Oct 2026, 1.6 to 2.1 times the highest of the original six). Fees are average revenue per parcel from the regulators (not consumer prices). Population is not on one definition: Greater London (ONS mid-2025), Ile-de-France region (INSEE 2023), Berlin city (register, 31 Dec 2025). Lane capacity and BPR are the same generic values as the other cities. London shift hours (7.3) and van capacity (126) come from the 2017 UCL round (72 addresses); Paris reuses the London round and the Amazon 8.4 h proxy; Berlin stops (126) and parcels (206) come from one company in a union-linked survey. The London Congestion Charge is GBP 18 per day since the start of 2026 (GBP 15 before), not GBP 15.

## Population cross-check against GHSL 2025

| city | GHSL bbox (M) | official (M) | definition | ratio GHSL/official |
|---|---|---|---|---|
| New Delhi | 25.015 | 30.2 | New Delhi urban agglomeration (UN degree-of-urbanisation definition) | 0.828 |
| Cairo | 14.927 | 25.6 | Cairo urban agglomeration (UN WUP 2025) | 0.583 |
| Moscow | 12.558 | 13.274 | Moscow city (federal city) | 0.946 |
| Buenos Aires | 13.255 | 13.986 | AMBA = CABA (3,120,612) + 24 partidos GBA (10,865,182) | 0.948 |
| New York | 12.121 | 20.112 | New York-Newark-Jersey City metro (CBSA) | 0.603 |
| Mumbai | 21.953 | 20.2 | Mumbai urban agglomeration (UN WUP 2025) | 1.087 |
| London | 11.283 | 9.123 | Greater London, ONS mid-2025 (mid-2024: 9.150) | 1.237 |
| Paris | 9.023 | 12.463 | Ile-de-France region, INSEE legal population 2023 (Paris commune 2.133; INSEE reference 1 Jan 2021) | 0.724 |
| Berlin | 4.655 | 3.914 | Berlin city, registered residents 31 Dec 2025 (Amt fuer Statistik) | 1.189 |

New York: the GHSL box (12.12M) is 1.41x the city of New York (8.597M, July 2024 estimate) and 0.60x the metro area (20.11M). Cairo: the box covers only 42 zones, hence 0.58 of the UN agglomeration. Delhi: 0.83 of the UN agglomeration (which extends beyond the NCT). Mumbai: 1.09, the box includes Thane/Navi Mumbai and WUP uses a contiguous high-density definition. Moscow and Buenos Aires are within 6% and 5%. These ratios are consistent with the GHSL zones being a reasonable population base, but the two NYC and Cairo ratios mean per-capita demand should be applied to the GHSL population, not to the official figure.

London, Paris, Berlin (added 2026-10-23): the **London** box holds 11.28M, 1.24 times Greater London (9.12M), so the box evidently covers Greater London plus part of the surrounding commuter ring (the box is 1.02 degrees wide and 0.43 high, about 71 km by 47 km); the share of the wider London metro region inside the box was not computed (no official metro figure retrieved). The **Paris** box holds 9.02M, which is 72% of the Ile-de-France region (12.46M) and 4.2 times the Paris commune (2.13M): it covers the dense core and inner ring but not the outer region. The **Berlin** box holds 4.65M, 1.19 times Berlin city (3.91M); the box (12.76 to 13.98 E, 52.23 to 52.82 N) also takes in Potsdam and the Brandenburg belt, and a Berlin-Brandenburg metro figure was not retrieved. As for New York and Cairo, apply per-capita demand to the GHSL population, not to the official figure. All three official figures are A or B quality, but the three definitions differ (city, region, city), so ratios are not comparable across the three.

## Recommended default calibration and plausible ranges (low / base / high)

Base equals the wide table. Low and high are for sensitivity analysis; the 'basis' column says whether a range is sourced or an explicit modelling assumption. Items marked 'assumed' are not statistics.

### parcels_per_capita_per_day

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 0.009 | 0.00964 | 0.0197 | low: Redseer 4.8bn e-commerce; high: all express 10.5bn (incl. hyperlocal/traditional). Urban uplift not included (x1.0-2.0 assumed). |
| Cairo | 0.0028 | 0.00561 | 0.0084 | assumed x0.5 / x1.5 around a single secondary estimate |
| Moscow | 0.12 | 0.1557 | 0.17 | low: assumed excl. cross-border/multi-item orders; high: Data Insight H1 2026 4.5bn parcels annualised to ~9bn |
| Buenos Aires | 0.0105 | 0.01505 | 0.0384 | low: assumed x0.7 (orders overstate parcels); high: CACE 645M units |
| New York | 0.165 | 0.1836 | 0.202 | assumed +/-10% around Pitney Bowes 67/yr |
| Mumbai | 0.009 | 0.00964 | 0.0197 | low: Redseer 4.8bn e-commerce; high: all express 10.5bn (incl. hyperlocal/traditional). Urban uplift not included (x1.0-2.0 assumed). |
| London | 0.1424 | 0.1661 | 0.2082 | low: Ofcom domestic parcels only (3.6bn); high: Pitney Bowes 2022 UK 76 parcels/person incl. returns (older edition) |
| Paris | 0.0498 | 0.065 | 0.0689 | low: ARCEP domestic parcels only (1,255M); high: incl. 100M exports (1,738M) |
| Berlin | 0.086 | 0.1434 | 0.1483 | low: B2C only (60% of BPEX total); high: Bundesnetzagentur 2024 company forecast 4.52bn (forecast, not outturn) |

### tomtom_congestion_pct

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 55.2 | 60.2 | 107.4 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| Cairo | 35.5 | 40.5 | 75.8 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| Moscow | 49 | 54 | 61 | base = TomTom 2020 (54); high = 61 (2021, secondary); low assumed |
| Buenos Aires | 43.1 | 48.1 | 78.7 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| New York | 43.8 | 48.8 | 79.3 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| Mumbai | 58.2 | 63.2 | 102.7 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| London | 46.6 | 51.6 | 79.5 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| Paris | 35 | 40 | 73 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |
| Berlin | 39.6 | 44.6 | 72.1 | low: base-5 pp (assumed, 2024-25 change was 2.5-3.5 pp); high: 2025 evening-rush congestion (TomTom) |

### tomtom_min_per_10km

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 21.6 | 24.0 | 31.75 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| Cairo | 20.1 | 22.38 | 28.43 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| Moscow | 20.0 | 25.0 | 28.6 | base: 24 km/h peak; low: assumed 30 km/h all-day; high: 21 km/h (10-point peak, Feb 2026) |
| Buenos Aires | 28.4 | 31.58 | 39.22 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| New York | 28.4 | 31.58 | 39.73 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| Mumbai | 26.0 | 28.85 | 35.5 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| London | 32.7 | 36.36 | 43.48 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| Paris | 27.0 | 30.0 | 37.97 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |
| Berlin | 26.1 | 28.99 | 34.68 | low: base x0.9 (assumed); high: 2025 evening-rush time (TomTom) |

### drops_per_vehicle_per_day

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 30 | 40 | 60 | Business Today 30-60 per executive; derived Valmo 30, Flipkart 40; Shadowfax 5.8 is a part-time-dominated floor |
| Cairo | 30 | 40 | 60 | Business Today 30-60 per executive; derived Valmo 30, Flipkart 40; Shadowfax 5.8 is a part-time-dominated floor |
| Moscow | 50 | 70 | 119 | low: assumed; base: London 72 addresses/round; high: Amazon US van 119 stops |
| Buenos Aires | 50 | 70 | 119 | low: assumed; base: London 72 addresses/round; high: Amazon US van 119 stops |
| New York | 72 | 120 | 128 | low: London round; base: Amazon 226 pkgs/1.9; high: 244 pkgs/1.9 |
| Mumbai | 30 | 40 | 60 | Business Today 30-60 per executive; derived Valmo 30, Flipkart 40; Shadowfax 5.8 is a part-time-dominated floor |
| London | 50 | 72 | 119 | low: assumed; base: UCL central London round 72 addresses (2017); high: Amazon US van 119 stops |
| Paris | 50 | 70 | 119 | low: assumed; base: London 72 addresses/round; high: Amazon US van 119 stops |
| Berlin | 72 | 126 | 128 | low: London round (three other German firms under 100 stops); base: one company in Verdi-linked survey (126 stops, 206 parcels); high: Amazon US upper value |

### shift_hours

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 8 | 10 | 12 | base: Zomato 10 h/day assumption; low/high assumed |
| Cairo | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem) |
| Moscow | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem) |
| Buenos Aires | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem) |
| New York | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem) |
| Mumbai | 8 | 10 | 12 | base: Zomato 10 h/day assumption; low/high assumed |
| London | 7.3 | 7.3 | 9.5 | base: UCL round duration (72 addresses, 2017); high: Amazon van rounds up to 9.5 h |
| Paris | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem) |
| Berlin | 7.5 | 8.4 | 9.5 | Amazon van rounds 7.5-9.5 h (8.4 avg incl. stem); 7.7 h/day (38.5 h/week) in DHL job ads, unverified |

### van_capacity_parcels

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 30 | 40 | 60 | two-wheeler dispatch load; assumption tied to daily drops (not found) |
| Cairo | 30 | 40 | 60 | two-wheeler dispatch load; assumption tied to daily drops (not found) |
| Moscow | 100 | 126 | 226 | low assumed; base London van 126; high Amazon van 226 observed |
| Buenos Aires | 100 | 126 | 226 | low assumed; base London van 126; high Amazon van 226 observed |
| New York | 126 | 226 | 244 | London 126; Amazon avg 226; Chicago 244 |
| Mumbai | 30 | 40 | 60 | two-wheeler dispatch load; assumption tied to daily drops (not found) |
| London | 100 | 126 | 226 | low assumed; base UCL London van 126; high Amazon van 226 observed |
| Paris | 100 | 126 | 226 | low assumed; base London van 126; high Amazon van 226 observed |
| Berlin | 126 | 206 | 226 | low London van 126; base 206 parcels per courier-day (one company, survey); high Amazon van 226 observed |

### delivery_fee_usd

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 0.6 | 0.69 | 1.0 | low: Shadowfax Rs 56.9/order; base Delhivery Rs 65.5; high assumed x1.45 |
| Cairo | 1.18 | 1.18 | 1.36 | EGP 65-75 (iDeliver pages) |
| Moscow | 1.8 | 3.67 | 4.89 | high: Ozon courier RUB 399; low assumed x0.5 (free-delivery thresholds) |
| Buenos Aires | 0.79 | 0.98 | 1.64 | Correo Argentino 1,200 / Andreani 1,500 / Mercado Envios 2,500 ARS |
| New York | 6.4 | 9.09 | 12.7 | assumed x0.7 / x1.4 (big-shipper contracts vs. residential/expedited) |
| Mumbai | 0.6 | 0.69 | 1.0 | as New Delhi |
| London | 2.95 | 4.21 | 5.89 | base: Ofcom GBP 13.2bn / 4.2bn parcels; Ofcom 2023-24 pair gives 4.46; low/high assumed x0.7 / x1.4 |
| Paris | 4.23 | 6.04 | 8.46 | base: ARCEP domestic revenue per parcel; all parcels incl. imports 5.74; low/high assumed x0.7 / x1.4 |
| Berlin | 3.08 | 4.4 | 4.94 | base: Bundesnetzagentur B2X revenue per parcel (2023); high: all parcels incl. cross-border; low assumed x0.7 |

### driver_wage_usd_per_hour

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 0.85 | 1.07 | 1.42 | low: union Rs 81/h; high: Zomato 2024 Rs 28,000/month /208 h |
| Cairo | 0.5 | 0.61 | 0.85 | low assumed informal; base min wage EGP 7,000; high Cairo avg salary EGP 9,780/208 h |
| Moscow | 3.5 | 4.53 | 8.6 | low assumed; base Dreamjob RUB 65k; high vc.ru bike courier RUB 100k at 5.5 h/day |
| Buenos Aires | 1.28 | 1.28 | 2.6 | floor = legal minimum; high assumed x2 for delivery-sector pay |
| New York | 21.57 | 22.27 | 28.0 | low: US median; base NY state median; high assumed (NYC metro/benefits) |
| Mumbai | 0.85 | 1.07 | 1.42 | as New Delhi |
| London | 17.02 | 18.76 | 19.02 | low: GBP 12.71 (Asda postings, unverified National Living Wage level); base: Indeed DPD GBP 14.01; high: Amazon Flex GBP 14.20 |
| Paris | 13.81 | 15.72 | 16.64 | low: SMIC EUR 12.31 from 1 Jun 2026; base: La Poste median EUR 25,500/yr at 1,820 h; high: senior EUR 27,000 |
| Berlin | 18.18 | 18.78 | 20.1 | low: gehalt.de Berlin median at 173.3 h/month; base: same at 2,080 h/yr; high: DHL collective rate EUR 17.92/h (job ads, unverified) |

### fuel_usd_per_litre

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 0.92 | 1.15 | 1.44 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| Cairo | 0.35 | 0.44 | 0.55 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| Moscow | 0.72 | 0.9 | 1.12 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| Buenos Aires | 1.16 | 1.45 | 1.81 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| New York | 0.98 | 1.22 | 1.52 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| Mumbai | 0.92 | 1.15 | 1.44 | assumed -20% / +25% (price and FX volatility); diesel is within this band |
| London | 1.87 | 2.34 | 2.93 | assumed -20% / +25% (price and FX volatility); diesel (2.67) is above the base |
| Paris | 1.94 | 2.42 | 3.03 | assumed -20% / +25% (price and FX volatility); diesel (2.64) is above the base |
| Berlin | 1.91 | 2.39 | 2.99 | assumed -20% / +25% (price and FX volatility); diesel (2.55) is above the base |

### n_major_carriers

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 4 | 5 | 6 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| Cairo | 3 | 4 | 5 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| Moscow | 2 | 5 | 6 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| Buenos Aires | 3 | 4 | 5 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| New York | 3 | 4 | 5 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| Mumbai | 4 | 5 | 6 | judgement; Moscow low 2 = effective competitors (Wildberries+Ozon 84% of parcels) |
| London | 4 | 5 | 6 | judgement; 6 before the Evri-DHL eCommerce merger (Sep 2025), 4 if Yodel/InPost is excluded |
| Paris | 4 | 5 | 6 | judgement; La Poste group (Colissimo, Chronopost, DPD) is one owner, Mondial Relay/InPost, Amazon, GLS, Relais Colis |
| Berlin | 4 | 6 | 6 | Bundesnetzagentur: six providers handle about 98% of parcels; low assumed |

### population_official_millions

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 16.8 | 30.2 | 30.2 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| Cairo | 10.4 | 25.6 | 25.6 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| Moscow | 13.0 | 13.274 | 13.3 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| Buenos Aires | 13.0 | 13.986 | 16.5 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| New York | 8.6 | 20.1 | 20.1 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| Mumbai | 12.44 | 20.2 | 22.1 | definition range: narrow administrative area vs. agglomeration (Delhi NCT 2011; BMC 2011; Cairo gov; NYC; Moscow 2021 census 13.0; AMBA 40 partidos 16.5; Macrotrends Mumbai 22.1) |
| London | 9.123 | 9.123 | 9.15 | Greater London ONS mid-2025 (9.123) and mid-2024 (9.150); no wider official metro figure retrieved |
| Paris | 2.133 | 12.463 | 12.463 | low: Paris commune (INSEE, reference 2021); base: Ile-de-France region 2023 |
| Berlin | 3.914 | 3.914 | 3.914 | Berlin city register 31 Dec 2025; Berlin-Brandenburg metro figure not retrieved |

### vehicles_per_1000_people

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 290 | 400 | 521 | from alternative denominators/sources in long table |
| Cairo | 103 | 220 | 273 | from alternative denominators/sources in long table |
| Moscow | 297 | 297 | 323 | from alternative denominators/sources in long table |
| Buenos Aires | 265 | 331 | 414 | from derivations in long table; Buenos Aires and New York low/high assumed -20%/+25% (Argentina national; NYC 2021) |
| New York | 200 | 242 | 290 | from derivations in long table; Buenos Aires and New York low/high assumed -20%/+25% (Argentina national; NYC 2021) |
| Mumbai | 250 | 330 | 406 | from alternative denominators/sources in long table |
| London | 288 | 288 | 330 | cars 288; all licensed vehicles incl. vans and motorcycles 330 (DfT Dec 2025 / ONS mid-2025) |
| Paris | 288 | 575 | 575 | base = France national cars per 1000 (proxy, overstates Paris); low = London ratio as a dense-city proxy (assumed) |
| Berlin | 275 | 330 | 334 | base: KBA/Destatis via dpa Jan 2026; 275 private cars (2025) and 334 all cars (Destatis, 2025) from search text, unverified |

### lane_capacity_veh_per_hour

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Cairo | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Moscow | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Buenos Aires | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| New York | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Mumbai | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| London | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Paris | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |
| Berlin | 700 | 1000 | 1900 | 1,900 pcphpl = saturation flow (FHWA/HCM); effective urban arterial ~ x0.4-0.55 (assumed green ratio); 1,900 upper bound |

### bpr_alpha

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Cairo | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Moscow | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Buenos Aires | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| New York | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Mumbai | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| London | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Paris | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |
| Berlin | 0.15 | 0.15 | 0.6 | 0.15 original BPR; 0.15-0.6 published recalibrations |

### bpr_beta

| city | low | base | high | basis |
|---|---|---|---|---|
| New Delhi | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Cairo | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Moscow | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Buenos Aires | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| New York | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Mumbai | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| London | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Paris | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |
| Berlin | 1.5 | 4 | 4 | 4 original BPR; recalibrations 1.2-3 (arXiv:2602.07811) and 1.54 (Indonesia) |

Change note for the ranges (2026-10-23): the low/base/high tables are per city, so adding London, Paris and Berlin did not change any of the six existing rows. Compared with the six-city span of base values, the new cities fall outside it for fuel (2.34 to 2.42 USD/L against 0.44 to 1.45), vehicles per 1000 (Paris 575 against 220 to 400, a national proxy), drops per vehicle (Berlin 126 against 40 to 120) and the driver wage (London 18.76, Paris 15.72 and Berlin 18.78 sit between New Delhi-Moscow and New York, so they are inside the 0.61 to 22.27 span). Only fuel and vehicles per 1000 therefore widen the nine-city span materially; the 'assumed -20%/+25%' fuel rule is unchanged but its absolute level for Europe is now about 1.9 to 3.0 USD/L. Items marked 'assumed' are not statistics.

Additional sensitivity items without a credible estimate: urban uplift factor on parcels per capita (not found; use 1.0 to 2.0, assumed; datapoints: India Tier-I and metro cities = 42% of e-commerce order volume in summer 2025 per Unicommerce, and Moscow region just under one fifth of Wildberries turnover in 2026), and price elasticity of delivery demand (not found; use -0.3 to -1.5, assumed).

## Weak numbers and country-level proxies (read before relying on them)

**Five weakest numbers**

1. **Egypt parcels per capita (0.0056/day)**: one paid-report summary (Ken Research, 220M parcels in 2025); no official statistic, and it is a country figure used for Cairo. (C)
2. **Moscow TomTom congestion 54% and 25 min per 10 km**: Moscow is not in the 2025 index; 54% is TomTom 2020 (secondary snippet) and the minutes are derived from a peak-hour speed of 24 km/h. (C)
3. **Driver wages for Cairo (USD 0.61/h), Buenos Aires (1.28), Moscow (4.53) and Delhi/Mumbai (1.07)**: minimum wage floors or job-site/gig averages, not courier payroll data; sources disagree by a factor of 2 or more in Moscow. (C)
4. **Drops per vehicle per day and van capacity outside the US**: India 40 (derived from a dated Business Today figure and company ratios), and Cairo/Moscow/Buenos Aires use India or London/Amazon proxies. Two-wheeler load capacity is an assumption. (C)
5. **Delivery fee for Cairo, Moscow, Buenos Aires**: a competitor's preview-site rate card, a consumer fee on one marketplace, and third-party reference rates; none is a carrier revenue per parcel. (C)

**Five weakest numbers for London, Paris and Berlin (added 2026-10-23)**

1. **Paris vehicles per 1000 (575)**: this is the France national passenger-car stock (39.7M cars / 69.08M people), not a Paris value. Only 31.8% of Paris households own a car (INSEE census 2022), so the proxy overstates Paris, probably by a factor of about two. (C)
2. **Berlin drops per vehicle (126) and van capacity (206 parcels)**: both come from one unnamed company in a union-linked national survey reported by Verkehrsrundschau (25 Nov 2025; year and sample not stated; three other companies were under 100 stops). Peak-heavy and not Berlin-specific. Berlin shift hours (8.4) are a US Amazon proxy. (C)
3. **Driver wages (London USD 18.76, Paris 15.72, Berlin 18.78)**: job-posting and salary-portal averages (Indeed DPD, Salerya, gehalt.de) converted to hourly rates with our own hour assumptions (1,820 h for France, 2,080 h for Germany); two of the three pages returned 403 or showed no data year, and Payscale disagrees with Indeed for London. No payroll statistic. (C)
4. **Paris drops (70), van capacity (126) and shift (8.4), plus London shift (7.3)**: Paris reuses the London 2017 round (72 addresses) and Amazon US 2018 vans; the London round is a single study of one next-day parcel round in central London. (C for Paris, B for London)
5. **UK delivery fee (USD 4.21) and UK carrier count/shares**: Ofcom's 2024-25 report returned HTTP 403, so GBP 13.2bn revenue and 4.2bn parcels come from search-result text and Pegasus Couriers; per-carrier shares for the UK are paywalled (Post & Parcel report) and not found; the UK carrier count (5) and the French count (5, with La Poste about 50% from one CEO quote) are judgements. (C)

**Country-level proxies**: all parcel volumes and e-commerce shares (India national for Delhi and Mumbai; Egypt; Russia; Argentina; US), fuel prices, driver-wage sources except New York state, delivery-fee sources, BPR parameters, lane capacity (generic), and the vehicle-per-1000 for Buenos Aires (Argentina national). New York drop, shift and capacity values come from Amazon vans in Austin, Boston, Chicago and Seattle (2018 data), not from New York.

**Country-level proxies for London, Paris and Berlin**: UK, France and Germany national parcel volumes (including B2B) and population denominators; Paris vehicles per 1000 (France national); regulator revenue per parcel instead of consumer fees; Berlin stops and parcels per courier (national survey); wages from national or job-posting averages; fuel, BPR and lane capacity.

**Not found**: city-specific BPR calibrations (a Delhi study exists, Shanbhog and Chand 2025, but alpha and beta are not in the abstract), city-specific lane capacity, vehicle operating cost per km outside the US (AAA private-car cost only), INRIX figures for Cairo, Moscow, Buenos Aires, Delhi and Mumbai, e-commerce share of retail for Egypt and Argentina, numeric delivery-demand price elasticity, urban uplift factors, market shares of most named carriers (Blue Dart, Ekart, Amazon Transport, CDEK, Russian Post, Andreani, OCA, Correo Argentino, Aramex today), NYC-specific stops per route, Moscow/Cairo/Buenos Aires congestion-charge or loading tariffs. Some secondary pages were seen only through search-result summaries (flagged in the notes), and the TomTom 'Metro' tab values were not extracted.

**Not found for London, Paris and Berlin**: INRIX hours lost per driver for Paris (only the -7% change vs 2024); TomTom highway speed in the City tab for London and Berlin (Metro tab values 77.7 and 70.3 km/h are in the CSV notes); UK per-carrier market shares (Royal Mail, Evri, DPD, DHL, Amazon, Yodel; paywalled) and Ofcom's own PDF (403); France per-carrier shares apart from La Poste about 50%, Amazon 15%, Mondial Relay 14% (Dec 2024 CEO statement) and no ARCEP operator split; Paris and Berlin stops per van round (proxies used) and cargo-bike share for all three cities; current Paris delivery-hour decree and Berlin loading-zone rules; a city-level vehicles per 1000 for Paris; INSEE aire d'attraction and Berlin-Brandenburg metro populations; UN WUP 2025 city values for the three cities; city-specific BPR calibrations and lane capacity; price elasticity; urban uplift factors; Germany diesel was read from the GlobalPetrolPrices page text (EUR 2.27, USD 2.55). TfL and Ofcom pages return 403 to this tool, so the London charge rates rely on Autoexpress and Drive.co.uk. The 2025 online share of retail for Germany (13.5%) and the EUR 92.3bn online turnover come from search-result text, not from the HDE press release itself.

**Other caveats**: (a) Redseer figures are Indian fiscal-year shipments, not calendar 2025. (b) Russian figures are orders, not parcels. (c) Argentine CACE figures are purchase orders (253M) and units (645M); parcels lie in between. (d) The Delhivery and Shadowfax revenues per shipment are carrier revenue (including B2B express), not consumer prices; Delhivery's express revenue (Rs 1,611 crore) comes from a press summary, the 246M shipments from the shareholder letter. (e) TomTom Egypt highway speed (37.9 km/h, 22.6 km/h slower than 2024) looks like a coverage artefact. (f) The USA gasoline price (1.22 USD/L) and other fuel prices are GlobalPetrolPrices values dated 2026-10-19.

## Urban freight and zone-charge policy facts

| city | policy | rate / rule | source |
|---|---|---|---|
| New York | zone_charge_car_peak_usd | 9.0 USD per day (E-ZPass, 5am-9pm weekdays, 9am-9pm weekends); Started 5 Jan 2025. Overnight $2.25 (-75%). Rises to $12 in 2028 and $15 in 2031. | [1] |
| New York | zone_charge_small_truck_peak_usd | 14.4 USD per entry (no daily cap); Overnight $3.60. Tolls-by-mail higher (large truck $32.40 peak). | [1] |
| New York | zone_charge_large_truck_peak_usd | 21.6 USD per entry; Overnight $5.40. Crossing credits up to $7.20 small trucks / $12 large trucks at tunnels. | [1] |
| New York | zone_charge_taxi_fhv_per_trip_usd | 0.75 taxi; 1.50 HV-FHV USD per trip; Per-trip charge paid by passenger. | [1] |
| New York | zone_charge_effect | 11 % fewer vehicle entries (Jan-Oct 2025); ~27M fewer vehicles; net revenue >$550M in year 1; VMT -7.1% in zone (Jan-Sep); morning crossing speeds +23%. Official claims; no independent audit seen. Useful for calibrating response to a zone charge. | [2] |
| Moscow | zone_charge_parking_rub_per_hour | 200 RUB per hour (max, 24 h) = USD 2.45; Boulevard Ring 80 RUB/h standard (150/h after 30 min flexible); Garden Ring-TTR 60 RUB/h. No cordon congestion charge; parking is the price instrument. Possible increase/occupancy-based rates since Dec 2025 not confirmed. | [3] |
| New Delhi | zone_charge | none in force -; No congestion charge adopted. Non-BS-VI/CNG/EV goods vehicles registered outside Delhi barred from 1 Nov 2025 (BS-IV allowed to 31 Oct 2026). Draft Logistics and Warehousing Policy 2025 not confirmed final. | [4] |
| Mumbai | zone_charge | none; peak-hour heavy-vehicle ban -; Heavy vehicles barred ~8-11 am and 5-9 pm; South Mumbai 7am-midnight except essentials. Exact hours differ between news reports; not light delivery vans/two-wheelers. No congestion charge. | [5] |
| Cairo | zone_charge | none found; daytime truck ban -; Trucks banned from main Cairo roads during daytime (Central Traffic Dept, 2014); current enforcement/hours unverified. No downtown parking tariff or congestion charge found. | [6] |
| Buenos Aires | zone_charge | none found; loading rules -; Trucks may load/unload in bus-only lanes 21:00-07:00, max 30 min (undated page). Macrocentro loading-hour regime from 2004 decrees; no congestion charge. Current 2025-26 tariffs not found. | [7] |
| London | zone_charge_congestion_gbp_per_day | 18 GBP per day (about USD 24.1; 21 if paid after midnight); Mon-Fri 07:00-18:00, weekends and bank holidays 12:00-18:00; was GBP 15 until end 2025; the 100% Cleaner Vehicle Discount ended 2 Jan 2026 (electric vans on Auto Pay 50% = GBP 9, electric cars 25%); no charge 25 Dec-1 Jan. | [117] [118] |
| London | zone_charge_ulez_gbp_per_day | 12.5 GBP per day (about USD 16.7) for non-compliant cars and vans (vans: petrol Euro 4, diesel Euro 6 needed); 24/7 except Christmas Day; covers all boroughs, not the M25. | [118] |
| Paris | zone_charge | none found (no cordon charge); ZTL Paris Centre since 5 Nov 2024, 24/7, arrondissements 1-4: transit banned, origin/destination traffic (including deliveries) allowed; ZFE in the Metropole du Grand Paris restricts Crit'Air 3-5 with a no-fine pedagogic period kept through 2026; the national ZFE repeal was struck down on 21 May 2026 (decision 2026-903 DC). | [119] [120] [121] |
| Paris | delivery_loading_rules | not found for 2025-26; older rules: delivery bays 30 min (2006), Montorgueil pedestrian zone deliveries 6:00-10:00 and 13:30-15:30 for vehicles under 20 m2 (2017). | [122] |
| Berlin | zone_charge | none found; Umweltzone inside the S-Bahn ring (about 88 sq km), 24/7, green sticker mandatory (red from 2008, green since 1 Jan 2010), EUR 100 fine for driving or parking without it, vans and trucks covered. Loading-zone rules not found. | [123] [124] |

## Full parameter table

Columns: value and unit, geography and year, quality, source with reference number (URLs below). Notes for C-quality rows are shortened here; full notes are in the CSV.

| city | parameter | value | unit | geography | year | Q | source | ref |
|---|---|---|---|---|---|---|---|---|
| New Delhi | tomtom_congestion_pct | 60.2 | % extra travel time vs free flow (all-day) | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_min_per_10km | 24.0 | min per 10 km (all-day avg) | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_rush_hour_speed_kmh | 20.8 | km/h | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_am_peak_congestion_pct | 71.7 | % | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_am_peak_min_per_10km | 25.97 | min per 10 km | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_pm_peak_congestion_pct | 107.4 | % | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_pm_peak_min_per_10km | 31.75 | min per 10 km | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_peak_hour_congestion_pct | 192 | % at 6 pm | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_hours_lost_rush_hour_per_year | 104 | hours per driver per year | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| New Delhi | tomtom_highway_speed_kmh | 48.1 | km/h | Delhi (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [8] |
| Mumbai | tomtom_congestion_pct | 63.2 | % extra travel time vs free flow (all-day) | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_min_per_10km | 28.85 | min per 10 km (all-day avg) | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_rush_hour_speed_kmh | 17.6 | km/h | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_am_peak_congestion_pct | 82.7 | % | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_am_peak_min_per_10km | 32.43 | min per 10 km | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_pm_peak_congestion_pct | 102.7 | % | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_pm_peak_min_per_10km | 35.5 | min per 10 km | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_peak_hour_congestion_pct | 129 | % at 6 pm | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_hours_lost_rush_hour_per_year | 126 | hours per driver per year | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Mumbai | tomtom_highway_speed_kmh | 54.1 | km/h | Mumbai (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [9] |
| Cairo | tomtom_congestion_pct | 40.5 | % extra travel time vs free flow (all-day) | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_min_per_10km | 22.38 | min per 10 km (all-day avg) | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_rush_hour_speed_kmh | 23.2 | km/h | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_am_peak_congestion_pct | 42.7 | % | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_am_peak_min_per_10km | 22.9 | min per 10 km | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_pm_peak_congestion_pct | 75.8 | % | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_pm_peak_min_per_10km | 28.43 | min per 10 km | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_peak_hour_congestion_pct | 122 | % at 5 pm | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_hours_lost_rush_hour_per_year | 74 | hours per driver per year | Cairo (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Cairo | tomtom_highway_speed_kmh | 37.9 | km/h | Cairo (TomTom city tab) | 2025 | B | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [10] |
| Buenos Aires | tomtom_congestion_pct | 48.1 | % extra travel time vs free flow (all-day) | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_min_per_10km | 31.58 | min per 10 km (all-day avg) | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_rush_hour_speed_kmh | 15.8 | km/h | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_am_peak_congestion_pct | 70.8 | % | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_am_peak_min_per_10km | 36.37 | min per 10 km | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_pm_peak_congestion_pct | 78.7 | % | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_pm_peak_min_per_10km | 39.22 | min per 10 km | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_peak_hour_congestion_pct | 144 | % at 5 pm | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_hours_lost_rush_hour_per_year | 126 | hours per driver per year | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| Buenos Aires | tomtom_highway_speed_kmh | 59.5 | km/h | Gran Buenos Aires (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [11] |
| New York | tomtom_congestion_pct | 48.8 | % extra travel time vs free flow (all-day) | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_min_per_10km | 31.58 | min per 10 km (all-day avg) | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_rush_hour_speed_kmh | 15.7 | km/h | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_am_peak_congestion_pct | 68.3 | % | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_am_peak_min_per_10km | 36.37 | min per 10 km | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_pm_peak_congestion_pct | 79.3 | % | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_pm_peak_min_per_10km | 39.73 | min per 10 km | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_peak_hour_congestion_pct | 147 | % at 3 pm | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_hours_lost_rush_hour_per_year | 125 | hours per driver per year | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| New York | tomtom_highway_speed_kmh | 44.1 | km/h | New York, NY (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [12] |
| Moscow | tomtom_congestion_pct | not found | % | Moscow | 2025 | B | TomTom Traffic Index 2025 ranking page (Moscow absent) | [13] |
| Moscow | tomtom_congestion_pct_proxy_2020 | 54 | % | Moscow agglomeration | 2020 | C | Katadata Databoks citing TomTom 2020 (via search result) | [14] |
| Moscow | tomtom_congestion_pct_proxy_2018 | 56 | % | Moscow | 2018 | C | The Moscow Times on TomTom 2018 index | [15] |
| Moscow | moscow_citywide_avg_speed_peak_kmh | 24 | km/h (evening peak, 8-9 points) | Moscow city | 2025 | C | Moscow Dept of Transport via Profile.ru (Dec 2025 evening; 21 km/h at 10 points Feb 2026) | [16] |
| Moscow | tomtom_min_per_10km | not found | min per 10 km | Moscow | 2025 | C | - |  |
| New York | inrix_hours_lost_per_driver | 102 | hours per driver per year | New York City urban area | 2025 | B | INRIX 2025 Global Traffic Scorecard (via INRIX press/blog summary) | [17] |
| New Delhi | inrix_hours_lost_per_driver | not found | hours | - | 2025 | C | INRIX 2025 Scorecard | [18] |
| Mumbai | inrix_hours_lost_per_driver | not found | hours | - | 2025 | C | INRIX 2025 Scorecard | [18] |
| Cairo | inrix_hours_lost_per_driver | not found | hours | - | 2025 | C | INRIX 2025 Scorecard | [18] |
| Moscow | inrix_hours_lost_per_driver | not found | hours | - | 2025 | C | INRIX 2025 Scorecard | [18] |
| Buenos Aires | inrix_hours_lost_per_driver | not found | hours | - | 2025 | C | INRIX 2025 Scorecard | [18] |
| New Delhi | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| New Delhi | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| New Delhi | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Cairo | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Cairo | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Cairo | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Moscow | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Moscow | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Moscow | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Buenos Aires | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Buenos Aires | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Buenos Aires | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| New York | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| New York | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| New York | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Mumbai | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Mumbai | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Mumbai | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| New Delhi | bpr_calibrated_city | not found (exists, values not accessible) | - | Delhi urban mid-block roads | 2025 | B | Shanbhog & Chand, Calibrating Volume Delay Functions for Urban Roads in Delhi (TPMDC 2024, Springer 2025) | [21] |
| Cairo | bpr_calibrated_city | not found | - | Cairo | 2025 | C | Literature search |  |
| Moscow | bpr_calibrated_city | not found | - | Moscow | 2025 | C | Literature search |  |
| Buenos Aires | bpr_calibrated_city | not found | - | Buenos Aires | 2025 | C | Literature search |  |
| New York | bpr_calibrated_city | not found | - | New York | 2025 | C | Literature search |  |
| Mumbai | bpr_calibrated_city | not found | - | Mumbai | 2025 | C | Literature search |  |
| New Delhi | population_official_millions | 30.2 | million | New Delhi urban agglomeration (UN degree-of-urbanisation definition) | 2025 | B | UN DESA World Urbanization Prospects 2025 (via CityGeographics table) | [22] |
| Cairo | population_official_millions | 25.6 | million | Cairo urban agglomeration (UN WUP 2025) | 2025 | B | UN DESA World Urbanization Prospects 2025 (via CityGeographics table) | [22] |
| Cairo | population_cairo_governorate | 10.4 | million | Cairo governorate | 2025 | B | CAPMAS population clock via Egypt Today/CairoScene | [23] |
| Moscow | population_official_millions | 13.274285 | million | Moscow city (federal city) | 2025 | A | Mosstat (Moscow statistics office) via Snob.ru/Expert.ru | [24] |
| Buenos Aires | population_official_millions | 13.985794 | million | AMBA = CABA (3,120,612) + 24 partidos GBA (10,865,182) | 2022 | B | INDEC Censo 2022 provisional counts (via Chequeado/Ambito, summed by us) | [25] |
| New York | population_official_millions | 20.112448 | million | New York-Newark-Jersey City metro (CBSA) | 2025 | B | US Census Bureau Vintage 2025 (via statranker table) | [26] |
| New York | population_nyc_city | 8.597 | million | New York City (5 boroughs) | 2024 | A | NYC Dept of City Planning, March 2026 report on Census Vintage 2025 | [27] |
| Mumbai | population_official_millions | 20.2 | million | Mumbai urban agglomeration (UN WUP 2025) | 2025 | B | UN DESA WUP 2025 (via CityGeographics) | [22] |
| New Delhi | population_ghsl_2025_millions | 25.015 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| New Delhi | population_ratio_ghsl_to_official | 0.828 | ratio | - | 2025 | B | computed |  |
| Cairo | population_ghsl_2025_millions | 14.927 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Cairo | population_ratio_ghsl_to_official | 0.583 | ratio | - | 2025 | B | computed |  |
| Moscow | population_ghsl_2025_millions | 12.558 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Moscow | population_ratio_ghsl_to_official | 0.946 | ratio | - | 2025 | B | computed |  |
| Buenos Aires | population_ghsl_2025_millions | 13.255 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Buenos Aires | population_ratio_ghsl_to_official | 0.948 | ratio | - | 2025 | B | computed |  |
| New York | population_ghsl_2025_millions | 12.121 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| New York | population_ratio_ghsl_to_official | 0.603 | ratio | - | 2025 | B | computed |  |
| Mumbai | population_ghsl_2025_millions | 21.953 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Mumbai | population_ratio_ghsl_to_official | 1.087 | ratio | - | 2025 | B | computed |  |
| New Delhi | population_national_millions | 1464 | million | India | 2025 | B | UNFPA State of World Population 2025 (1.46 billion) | [28] |
| Cairo | population_national_millions | 107.5 | million | Egypt | 2025 | B | CAPMAS population clock via CairoScene (Apr 2025; 109.54M by Sep 2026) | [23] |
| Moscow | population_national_millions | 146.028 | million | Russia | 2025 | A | Rosstat preliminary 1 Jan 2025 via TASS | [29] |
| Buenos Aires | population_national_millions | 46.044703 | million | Argentina | 2022 | A | INDEC Censo 2022 | [30] |
| New York | population_national_millions | 341.784857 | million | United States | 2025 | A | US Census Bureau Vintage 2025 (via search of QuickFacts table) | [31] |
| Mumbai | population_national_millions | 1464 | million | India | 2025 | B | UNFPA State of World Population 2025 | [28] |
| New Delhi | parcels_national_per_year_bn | 5.15 | billion shipments (e-commerce, FY2025) | India | 2025 | B | Redseer 'Express Logistics in Motion' via Storyboard18 (Apr 2025) | [32] |
| New Delhi | parcels_express_total_per_year_bn | 10.5 | billion shipments (all express, FY2025) | India | 2025 | B | Redseer via Storyboard18 | [32] |
| New Delhi | parcels_per_capita_per_year | 3.52 | parcels/person/yr | India (national) | 2025 | B | derived: Redseer e-commerce shipments / UNFPA population |  |
| New Delhi | parcels_per_capita_per_day | 0.00964 | parcels/person/day | India (national) | 2025 | B | derived |  |
| Mumbai | parcels_per_capita_per_year | 3.52 | parcels/person/yr | India (national) | 2025 | B | derived: Redseer e-commerce shipments / UNFPA population |  |
| Mumbai | parcels_per_capita_per_day | 0.00964 | parcels/person/day | India (national) | 2025 | B | derived |  |
| Cairo | parcels_national_per_year_mn | 220 | million parcels | Egypt | 2025 | C | Ken Research Egypt smart logistics & e-commerce warehousing market (estimate) | [33] |
| Cairo | parcels_per_capita_per_year | 2.05 | parcels/person/yr | Egypt (national) | 2025 | C | derived: Ken Research / CAPMAS population |  |
| Cairo | parcels_per_capita_per_day | 0.00561 | parcels/person/day | Egypt (national) | 2025 | C | derived |  |
| Moscow | orders_national_per_year_bn | 8.3 | billion online orders | Russia | 2025 | B | Data Insight via Selsup.ru review (+24% y/y; avg order ~1,600 RUB) | [34] |
| Moscow | parcels_per_capita_per_year | 56.8 | orders/person/yr | Russia (national) | 2025 | B | derived |  |
| Moscow | parcels_per_capita_per_day | 0.15572 | parcels/person/day | Russia (national) | 2025 | B | derived |  |
| Buenos Aires | orders_national_per_year_mn | 253 | million purchase orders | Argentina | 2025 | B | CACE Estudio Anual 2025 (via Mercado.com.ar) | [35] |
| Buenos Aires | units_sold_national_mn | 645 | million product units | Argentina | 2025 | B | CACE preliminary 2025 report (via Mercado.com.ar) | [36] |
| Buenos Aires | parcels_per_capita_per_year | 5.49 | orders/person/yr | Argentina (national) | 2025 | B | derived: CACE orders / INDEC population |  |
| Buenos Aires | parcels_per_capita_per_day | 0.01505 | parcels/person/day | Argentina (national) | 2025 | B | derived |  |
| New York | parcels_per_person_per_year | 67 | parcels/person/yr | United States (national) | 2025 | B | Pitney Bowes Parcel Shipping Index 2025 (23.1bn parcels) | [37] |
| New York | parcels_per_capita_per_year | 67 | parcels/person/yr | United States (national) | 2025 | B | Pitney Bowes Parcel Shipping Index 2025 | [37] |
| New York | parcels_per_capita_per_day | 0.18356 | parcels/person/day | United States (national) | 2025 | B | derived |  |
| New Delhi | ecommerce_share_of_retail_pct | 7 | % of retail (range 5-9) | India | 2025 | C | McKinsey (via Times of Oman) 7-9% FY23; NISM compilation 8-9%; Bain-based ~5% (own arithmetic in search) | [38] |
| Mumbai | ecommerce_share_of_retail_pct | 7 | % of retail (range 5-9) | India | 2025 | C | as New Delhi | [38] |
| Cairo | ecommerce_share_of_retail_pct | not found | % | Egypt | 2025 | C | - |  |
| Moscow | ecommerce_share_of_retail_pct | 18.8 | % of retail turnover | Russia | 2025 | B | AKIT via Capital FM (up from 16.2% in 2024) | [39] |
| Buenos Aires | ecommerce_share_of_retail_pct | not found | % | Argentina | 2025 | C | - |  |
| New York | ecommerce_share_of_retail_pct | 17.1 | % of retail (SA, Q2 2026) | United States | 2026 | A | US Census Bureau Quarterly Retail E-Commerce Sales Q2 2026 (via Economy Insights / FRED) | [40] |
| New Delhi | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Cairo | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Moscow | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Buenos Aires | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| New York | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Mumbai | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| New York | packages_per_route_day | 226 | packages per van round (range 213-244 across 4 US cities) | US cities (Amazon vans) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | packages_per_stop | 1.9 | packages/stop | US cities (Amazon vans) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | drops_per_vehicle_per_day | 120 | stops per van per day | US cities (Amazon vans) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | shift_hours | 8.4 | hours (7.5 excl. stem time) | US cities (Amazon vans) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | service_time_per_stop_s | 154 | seconds per stop (mean; P50 102 s; city means 115-178 s) | US cities (Amazon vans, Table 4: planned service time, in-city) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | travel_time_between_stops_s | 80 | seconds (mean; SD 74) | US cities (Amazon vans, Table 3) | 2018 | B | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New York | service_time_per_stop_london_min | 8.1 | minutes dwell per vehicle stop (central London) | London | 2018 | C | Allen et al. 2018 via MapAtlas blog (secondary) | [42] |
| New York | london_van_round | 126 | parcels per van round (72 addresses, 7.3 h) | central London | 2017 | B | UCL portering study of next-day parcel round | [43] |
| New York | van_capacity_parcels | 226 | parcels per van load (observed, lower bound of capacity) | US cities (Amazon vans) | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| New Delhi | drops_per_vehicle_per_day | 40 | parcels per delivery executive per day (two-wheeler); range 30-60 | India metros | 2025 | C | Derived: Business Today (50-60 in metros, older); Valmo 9 lakh orders/30k executives=30; Flipkart 800k/20k=40 | [44] |
| New Delhi | packages_per_partner_per_day_shadowfax | 5.83 | packages/partner/day | India (Shadowfax network) | 2025 | B | Shadowfax Annual Report FY2024-25 (1.2 Mn packages delivered daily; 205,864 avg quarterly active delivery part | [45] |
| Mumbai | drops_per_vehicle_per_day | 40 | parcels per delivery executive per day; range 30-60 | India metros | 2025 | C | as New Delhi | [44] |
| New Delhi | shift_hours | 10 | hours/day (gig platform assumption) | India | 2025 | C | Zomato CEO calculation (10 h/day, 26 days) via Restaurant India | [46] |
| Mumbai | shift_hours | 10 | hours/day | India | 2025 | C | as New Delhi | [46] |
| New Delhi | van_capacity_parcels | 40 | parcels per two-wheeler dispatch (assumption = daily drops) | India | 2025 | C | assumption; BigBasket max executive load 15 kg (Gulf News/BT) | [44] |
| Mumbai | van_capacity_parcels | 40 | parcels per two-wheeler dispatch (assumption) | India | 2025 | C | assumption |  |
| Cairo | drops_per_vehicle_per_day | 40 | stops per vehicle per day (PROXY) | proxy: India two-wheeler | 2025 | C | proxy |  |
| Cairo | shift_hours | 8.4 | hours (PROXY) | proxy US vans | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| Cairo | van_capacity_parcels | 40 | parcels (PROXY) | proxy | 2025 | C | proxy (India two-wheeler / London van) |  |
| Moscow | drops_per_vehicle_per_day | 70 | stops per vehicle per day (PROXY) | proxy: London van round (72 addresses) | 2025 | C | proxy |  |
| Moscow | shift_hours | 8.4 | hours (PROXY) | proxy US vans | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| Moscow | van_capacity_parcels | 126 | parcels (PROXY) | proxy | 2025 | C | proxy (India two-wheeler / London van) |  |
| Buenos Aires | drops_per_vehicle_per_day | 70 | stops per vehicle per day (PROXY) | proxy: London van round | 2025 | C | proxy |  |
| Buenos Aires | shift_hours | 8.4 | hours (PROXY) | proxy US vans | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city r | [41] |
| Buenos Aires | van_capacity_parcels | 126 | parcels (PROXY) | proxy | 2025 | C | proxy (India two-wheeler / London van) |  |
| Mumbai | vehicle_mix_two_wheelers_pct | 59.34 | % of registered vehicles | Mumbai | 2025 | A | BMC vehicle population report (Mar 2025) via The Week/PTI | [47] |
| New Delhi | vehicle_mix_two_wheelers_pct | 66 | % of registered vehicles | Delhi NCT | 2019 | C | Delhi Economic Survey 2018-19 (via search summary) | [48] |
| Cairo | vehicle_mix_cars_pct | 54.1 | % of licensed vehicles (trucks/trailers 12.2%) | Egypt | 2025 | B | CAPMAS via Ahram Online | [49] |
| Moscow | vehicle_mix | not found | - | Moscow | 2025 | C | - |  |
| Buenos Aires | vehicle_mix | not found | - | Buenos Aires | 2025 | C | - |  |
| New York | vehicle_mix | not found | - | New York | 2025 | C | - |  |
| New Delhi | vehicles_per_1000_people | 400 | registered motor vehicles per 1000 (range 290-521) | Delhi | 2026 | C | Delhi Economic Survey 2025-26 vehicle population 87.6 lakh (via Motorbeam, unverified) / population WUP 30.2M  | [50] |
| Mumbai | vehicles_per_1000_people | 330 | registered vehicles per 1000 (range 250-406) | Mumbai | 2025 | C | BMC 5,054,907 vehicles Mar 2025 / pop 12.44M (Census 2011) to 20.2M (WUP) | [47] |
| Cairo | vehicles_per_1000_people | 220 | licensed vehicles per 1000 (range 103-273) | Cairo+Giza | 2025 | C | CAPMAS via Ahram (Cairo 2.84M, Giza 1.6M; Egypt 11.05M) / governorate pops 10.4M, 9.7M | [49] |
| Moscow | vehicles_per_1000_people | 297 | passenger cars per 1000 | Moscow city | 2025 | B | Autostat-Info 3.94M cars (start 2025) via Autonews / Mosstat 13.274M | [51] |
| Buenos Aires | vehicles_per_1000_people | 331 | vehicles per 1000 (national) | Argentina | 2024 | B | AFAC fleet report via Infobae (15.55M vehicles; 3.02 people/vehicle) | [52] |
| New York | vehicles_per_1000_people | 242 | registered vehicles owned by NYC residents per 1000 | New York City | 2021 | C | Streetsblog/Komanoff from Census data (2.077M vehicles 2021) / 8.597M | [53] |
| New York | car_free_households_pct | 53.9 | % households | New York City | 2021 | B | Streetsblog/Komanoff (Census) | [53] |
| New Delhi | fx_local_per_usd | 94.901331 | INR per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Mumbai | fx_local_per_usd | 94.901331 | INR per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Cairo | fx_local_per_usd | 55.215592 | EGP per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Moscow | fx_local_per_usd | 81.520547 | RUB per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Buenos Aires | fx_local_per_usd | 1527.8511 | ARS per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| New York | fx_local_per_usd | 1.0 | USD per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| New Delhi | fuel_gasoline_usd_per_litre | 1.15 | USD/L (Octane-95) | India | 2026 | B | GlobalPetrolPrices.com (Petroleum Planning & Analysis Cell data via GlobalPetrolPrices) | [55] |
| New Delhi | fuel_diesel_usd_per_litre | 1.04 | USD/L | India | 2026 | B | GlobalPetrolPrices.com | [56] |
| Mumbai | fuel_gasoline_usd_per_litre | 1.15 | USD/L (Octane-95) | India | 2026 | B | GlobalPetrolPrices.com (Petroleum Planning & Analysis Cell data via GlobalPetrolPrices) | [55] |
| Mumbai | fuel_diesel_usd_per_litre | 1.04 | USD/L | India | 2026 | B | GlobalPetrolPrices.com | [56] |
| Cairo | fuel_gasoline_usd_per_litre | 0.44 | USD/L (Octane-95) | Egypt | 2026 | A | GlobalPetrolPrices.com (Ministry of Petroleum and Mineral Resources via GlobalPetrolPrices) | [57] |
| Cairo | fuel_diesel_usd_per_litre | 0.38 | USD/L | Egypt | 2026 | B | GlobalPetrolPrices.com | [58] |
| Moscow | fuel_gasoline_usd_per_litre | 0.9 | USD/L (Octane-95) | Russia | 2026 | A | GlobalPetrolPrices.com (Rosstat via GlobalPetrolPrices) | [59] |
| Moscow | fuel_diesel_usd_per_litre | 0.98 | USD/L | Russia | 2026 | B | GlobalPetrolPrices.com | [60] |
| Buenos Aires | fuel_gasoline_usd_per_litre | 1.45 | USD/L (Octane-95) | Argentina | 2026 | A | GlobalPetrolPrices.com (Secretaria de Energia via GlobalPetrolPrices) | [61] |
| Buenos Aires | fuel_diesel_usd_per_litre | 1.62 | USD/L | Argentina | 2026 | B | GlobalPetrolPrices.com | [62] |
| New York | fuel_gasoline_usd_per_litre | 1.22 | USD/L (Octane-95) | USA | 2026 | A | GlobalPetrolPrices.com (US EIA via GlobalPetrolPrices) | [63] |
| New York | fuel_diesel_usd_per_litre | 1.66 | USD/L | USA | 2026 | B | GlobalPetrolPrices.com | [64] |
| New York | vehicle_operating_cost_usd_per_mile | 0.77 | USD per mile (15,000 mi/yr; $1.00 at 10k, $0.66 at 20k) | United States (private new vehicle) | 2025 | B | AAA Your Driving Costs 2025 (via AAA newsroom summary) | [65] |
| New Delhi | vehicle_operating_cost_per_km | not found | - | India | 2025 | C | - |  |
| Mumbai | vehicle_operating_cost_per_km | not found | - | India | 2025 | C | - |  |
| Cairo | vehicle_operating_cost_per_km | not found | - | Egypt | 2025 | C | - |  |
| Moscow | vehicle_operating_cost_per_km | not found | - | Russia | 2025 | C | - |  |
| Buenos Aires | vehicle_operating_cost_per_km | not found | - | Argentina | 2025 | C | - |  |
| New York | driver_wage_usd_per_hour | 22.27 | USD/h median light-truck driver (New York state; US 21.57) | New York state | 2025 | B | BLS OEWS wage data via O*NET OnLine (SOC 53-3033) | [66] |
| New Delhi | driver_wage_usd_per_hour | 1.07 | USD/h (Rs 102/h) | India (Zomato partners, national) | 2025 | C | Zomato-reported average partner earnings Rs 102/h (2025) via Restaurant India | [46] |
| Mumbai | driver_wage_usd_per_hour | 1.07 | USD/h | India (national proxy) | 2025 | C | as New Delhi | [46] |
| Cairo | driver_wage_usd_per_hour | 0.61 | USD/h (EGP 7,000/month / 208 h) | Egypt (private-sector minimum wage) | 2025 | C | National Council for Wages via CairoScene; 208 h = 26 d x 8 h (our assumption) | [67] |
| Moscow | driver_wage_usd_per_hour | 4.53 | USD/h (RUB 65,000/month / 176 h) | Moscow courier | 2026 | C | Dreamjob.ru salary service (134 salaries, Moscow courier RUB 65,000) | [68] |
| Buenos Aires | driver_wage_usd_per_hour | 1.28 | USD/h (ARS 1,956/h) | Argentina (legal minimum hourly wage, Oct 2026) | 2026 | C | SMVM Resolucion 4/2026 via El Cronista | [69] |
| New Delhi | delivery_fee_usd | 0.69 | USD per express parcel (Rs 65.5 = Express revenue Rs 1,611 cr / 246M shipments, Q2 FY26) | India (Delhivery) | 2026 | B | Delhivery Q2FY26 shareholder letter (246M shipments) and express revenue Rs 1,611 cr (Share.Market/press) | [70] |
| Mumbai | delivery_fee_usd | 0.69 | USD per express parcel | India (Delhivery) | 2026 | B | as New Delhi | [70] |
| Cairo | delivery_fee_usd | 1.18 | USD per shipment (EGP 65; Cairo/Giza 24 h) | Cairo/Giza (iDeliver rate card) | 2026 | C | iDeliver pricing preview page (competitor of Bosta) | [71] |
| Moscow | delivery_fee_usd | 3.67 | USD per order (RUB 299 pickup-point; 399 courier = 4.89) | Russia (Ozon fee for non-prepaid / low-value orders) | 2026 | C | Snob.ru on Ozon delivery fee change | [72] |
| Buenos Aires | delivery_fee_usd | 0.98 | USD per 1 kg parcel (Andreani ARS 1,500; Correo Argentino ARS 1,200 = 0.79; Mercado Envios from ARS 2,500 = 1.64) | Argentina (CABA, reference rates) | 2026 | C | YoFacturo shipping cost guide 2026; third-party Mercado Libre shipping calculator | [73] |
| New York | delivery_fee_usd | 9.09 | USD average revenue per parcel (all carriers) | United States | 2024 | B | Pitney Bowes Parcel Shipping Index (10th ed.) via Digital Commerce 360 | [74] |
| New Delhi | n_major_carriers | 5 | count (Delhivery incl. Ecom Express, Shadowfax, Blue Dart, Ekart, Amazon Transport) | India | 2025 | C | judgement from Delhivery/Shadowfax/Redseer sources | [70] |
| Mumbai | n_major_carriers | 5 | count | India | 2025 | C | as New Delhi | [45] |
| Cairo | n_major_carriers | 4 | count (Aramex, Bosta, Mylerz, R2S; Egypt Post) | Egypt | 2025 | C | Parcel & Postal Technology Intl (2022); Ken Research; Ahram | [75] |
| Moscow | n_major_carriers | 5 | count (Wildberries, Ozon, Yandex Market, CDEK, Russian Post; also 5Post) | Russia | 2025 | B | Data Insight H1 2026 via Unisender; Selsup | [76] |
| Buenos Aires | n_major_carriers | 4 | count (Mercado Envios/Mercado Libre, Andreani, Correo Argentino, OCA; also Cabify Logistics 5.8M parcels 2025) | Argentina | 2025 | C | Develop Argentina; Forbes Argentina; Infonegocios | [77] |
| New York | n_major_carriers | 4 | count (USPS, Amazon Logistics, UPS, FedEx) | United States | 2025 | B | Pitney Bowes Parcel Shipping Index 2025; 2024 edition via DC360 | [37] |
| New Delhi | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Mumbai | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Cairo | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Moscow | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Buenos Aires | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| New York | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| New York | zone_charge_car_peak_usd | 9.0 | USD per day (E-ZPass, 5am-9pm weekdays, 9am-9pm weekends) | Manhattan south of and incl. 60th St | 2025 | A | MTA Congestion Relief Zone toll page | [1] |
| New York | zone_charge_small_truck_peak_usd | 14.4 | USD per entry (no daily cap) | Manhattan CRZ | 2025 | A | MTA | [1] |
| New York | zone_charge_large_truck_peak_usd | 21.6 | USD per entry | Manhattan CRZ | 2025 | A | MTA | [1] |
| New York | zone_charge_taxi_fhv_per_trip_usd | 0.75 taxi; 1.50 HV-FHV | USD per trip | Manhattan CRZ | 2025 | A | MTA | [1] |
| New York | zone_charge_effect | 11 | % fewer vehicle entries (Jan-Oct 2025); ~27M fewer vehicles; net revenue >$550M in year 1 | Manhattan CRZ | 2025 | B | MTA / NY Governor first-anniversary release (5 Jan 2026) via CITTI | [2] |
| Moscow | zone_charge_parking_rub_per_hour | 200 | RUB per hour (max, 24 h) = USD 2.45 | 133 busiest central streets inside TTR | 2025 | B | mos.ru official guide to paid parking (undated); Snob.ru Dec 2025 on increases | [3] |
| New Delhi | zone_charge | none in force | - | Delhi | 2026 | B | CAQM Direction 88 (23 Apr 2025, amended 17 Oct 2025); AsiaNews on congestion-pricing advice (Mar 2026) | [4] |
| Mumbai | zone_charge | none; peak-hour heavy-vehicle ban | - | Mumbai | 2026 | C | Moneylife / Curly Tales on Mumbai Traffic Police rules from 1 Feb 2026 | [5] |
| Cairo | zone_charge | none found; daytime truck ban | - | Cairo | 2025 | C | Ahram Online / Egyptian Streets (2014 report; 2025 CairoScene repost) | [6] |
| Buenos Aires | zone_charge | none found; loading rules | - | Buenos Aires (CABA) | 2024 | C | GCBA 'Logistica Nocturna en Carriles Exclusivos' | [7] |
| London | tomtom_congestion_pct | 51.6 | % extra travel time vs free flow (all-day) | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_min_per_10km | 36.36 | min per 10 km (all-day avg) | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_rush_hour_speed_kmh | 14.1 | km/h | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_am_peak_congestion_pct | 74.7 | % | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_am_peak_min_per_10km | 41.67 | min per 10 km | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_pm_peak_congestion_pct | 79.5 | % | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_pm_peak_min_per_10km | 43.48 | min per 10 km | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_peak_hour_congestion_pct | 138 | % at 5 pm | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_hours_lost_rush_hour_per_year | 141 | hours per driver per year | London (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| London | tomtom_highway_speed_kmh | not found | km/h | London (TomTom city tab) | 2025 | C | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [79] |
| Paris | tomtom_congestion_pct | 40.0 | % extra travel time vs free flow (all-day) | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_min_per_10km | 30.0 | min per 10 km (all-day avg) | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_rush_hour_speed_kmh | 16.9 | km/h | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_am_peak_congestion_pct | 60.4 | % | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_am_peak_min_per_10km | 32.97 | min per 10 km | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_pm_peak_congestion_pct | 73.0 | % | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_pm_peak_min_per_10km | 37.97 | min per 10 km | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_peak_hour_congestion_pct | 116 | % at 6 pm | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_hours_lost_rush_hour_per_year | 109 | hours per driver per year | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Paris | tomtom_highway_speed_kmh | 51.7 | km/h | Paris (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [80] |
| Berlin | tomtom_congestion_pct | 44.6 | % extra travel time vs free flow (all-day) | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_min_per_10km | 28.99 | min per 10 km (all-day avg) | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_rush_hour_speed_kmh | 18.1 | km/h | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_am_peak_congestion_pct | 58.7 | % | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_am_peak_min_per_10km | 31.58 | min per 10 km | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_pm_peak_congestion_pct | 72.1 | % | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_pm_peak_min_per_10km | 34.68 | min per 10 km | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_peak_hour_congestion_pct | 101 | % at 4 pm | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_hours_lost_rush_hour_per_year | 100 | hours per driver per year | Berlin (TomTom city tab) | 2025 | A | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| Berlin | tomtom_highway_speed_kmh | not found | km/h | Berlin (TomTom city tab) | 2025 | C | TomTom Traffic Index 2025 (city page, 'City' tab = central city area) | [81] |
| London | inrix_hours_lost_per_driver | 91 | hours per driver per year | London | 2025 | B | INRIX 2025 Global Traffic Scorecard, UK press release (London delays -10% vs 2024) | [82] |
| Paris | inrix_hours_lost_per_driver | not found | hours | Paris | 2025 | C | INRIX 2025 Global Traffic Scorecard | [18] |
| Berlin | inrix_hours_lost_per_driver | 60 | hours per driver per year | Berlin | 2025 | B | INRIX 2025 Global Traffic Scorecard, Germany press release (delays +3% vs 2024) | [83] |
| London | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| London | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| London | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| London | bpr_calibrated_city | not found | - | London | 2025 | C | Literature search (not repeated in depth for this extension) |  |
| Paris | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Paris | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Paris | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Paris | bpr_calibrated_city | not found | - | Paris | 2025 | C | Literature search (not repeated in depth for this extension) |  |
| Berlin | bpr_alpha | 0.15 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Berlin | bpr_beta | 4 | - | generic (US BPR) | 1964 | B | US Bureau of Public Roads (1964) default, as cited in arXiv:1802.09335 and others | [19] |
| Berlin | lane_capacity_veh_per_hour | 1000 | veh/h/lane (effective, signalised urban arterial) | generic | 2025 | C | Derived: FHWA HPMS base saturation flow 1,900 pcphpl (HCM 2000) x assumed green ratio ~0.5 | [20] |
| Berlin | bpr_calibrated_city | not found | - | Berlin | 2025 | C | Literature search (not repeated in depth for this extension) |  |
| London | population_official_millions | 9.122909 | million | Greater London (33 boroughs), mid-year estimate | 2025 | A | ONS mid-year population estimates (Nomis dataset NM_2002_1, London, mid-2025) | [95] |
| London | population_london_mid2024 | 9.149646 | million | Greater London, mid-year estimate | 2024 | A | ONS mid-year population estimates (Nomis dataset NM_2002_1, London, mid-2024) | [95] |
| Paris | population_official_millions | 12.463067 | million | Ile-de-France region (INSEE legal population 2023) | 2023 | B | INSEE populations legales, via CCI Paris Ile-de-France fact sheet | [98] |
| Paris | population_paris_commune | 2.133111 | million | Paris commune (municipal population, legal population in force 1 Jan 2024, reference date 1 Jan 2021) | 2021 | A | INSEE populations legales, department 75 table (Dec 2023) | [97] |
| Berlin | population_official_millions | 3.913644 | million | Berlin (Land = city), registered main residents 31 Dec 2025 | 2025 | A | Amt fuer Statistik Berlin-Brandenburg, Einwohnerregisterstatistik press release 16/2026 | [101] |
| London | population_ghsl_2025_millions | 11.283 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Paris | population_ghsl_2025_millions | 9.023 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| Berlin | population_ghsl_2025_millions | 4.655 | million | GHSL bbox used by simulation | 2025 | A | GHSL GHS-POP R2023A epoch 2025 (data/processed/<city>/meta.json population_zones_total) |  |
| London | population_ratio_ghsl_to_official | 1.237 | ratio | - | 2025 | B | computed (11.283 / 9.123) |  |
| Paris | population_ratio_ghsl_to_official | 0.724 | ratio | - | 2025 | B | computed (9.023 / 12.463) |  |
| Berlin | population_ratio_ghsl_to_official | 1.189 | ratio | - | 2025 | B | computed (4.655 / 3.914) |  |
| London | population_national_millions | 69.2814 | million | United Kingdom | 2024 | A | ONS mid-2024 UK population estimate (published 26 Sep 2025) | [96] |
| Paris | population_national_millions | 69.082 | million | France (incl. overseas departments), provisional 1 Jan 2026 | 2026 | B | INSEE population au 1er janvier (bilan demographique 2025, published 13 Jan 2026) | [99] |
| Berlin | population_national_millions | 83.5 | million | Germany, end of 2025 | 2025 | A | Destatis press release 203/2026 (16 Jun 2026) | [100] |
| London | parcels_national_per_year_bn | 4.2 | billion parcels (measured, domestic + inbound international) | United Kingdom, FY2024-25 | 2025 | B | Ofcom Post monitoring report 2024-25 (published 3 Dec 2025); figure also reproduced by Pegasus Couriers | [84] |
| London | parcels_per_capita_per_year | 60.6 | parcels/person/yr | United Kingdom (national) | 2025 | B | derived: Ofcom 4.2bn / ONS mid-2024 UK population 69.28M |  |
| London | parcels_per_capita_per_day | 0.16609 | parcels/person/day | United Kingdom (national) | 2025 | B | derived |  |
| Paris | parcels_national_per_year_mn | 1638 | million parcels delivered in France (ordinary, express and small packets; incl. 383M imports) | France | 2024 | A | ARCEP Observatoire du courrier et du colis 2024 (published 14 Oct 2025) | [86] |
| Paris | parcels_per_capita_per_year | 23.71 | parcels/person/yr | France (national) | 2024 | B | derived: ARCEP 1,638M / INSEE population 69.08M |  |
| Paris | parcels_per_capita_per_day | 0.06496 | parcels/person/day | France (national) | 2024 | B | derived |  |
| Berlin | parcels_national_per_year_bn | 4.37 | billion KEP shipments (courier, express, parcel; B2B + B2C + C2C) | Germany | 2025 | B | BPEX (formerly BIEK) KEP-Studie 2026 (published 23 Jun 2026), via Logistik Heute | [87] |
| Berlin | parcels_national_per_year_bn_bnetza_2023 | 4.36 | billion parcels (domestic 3.86bn + cross-border 0.50bn) | Germany | 2023 | A | Bundesnetzagentur Parcels Market Report 2024 (published 10 Jun 2025) | [89] |
| Berlin | parcels_per_capita_per_year | 52.34 | parcels/person/yr | Germany (national) | 2025 | B | derived: BPEX 4.37bn / Destatis population 83.5M |  |
| Berlin | parcels_per_capita_per_day | 0.14338 | parcels/person/day | Germany (national) | 2025 | B | derived |  |
| London | ecommerce_share_of_retail_pct | 27.5 | % of retail (internet sales share, 2025 annual average) | Great Britain | 2025 | A | ONS Retail Sales Index series J4MC (CSV download; Sep 2026 monthly value 28.3) | [90] |
| Paris | ecommerce_share_of_retail_pct | 12 | % of total retail trade (products and services sold online EUR 196.4bn, 3.2bn transactions) | France | 2025 | C | Fevad annual review 2025 via Ecommerce Nation | [91] |
| Berlin | ecommerce_share_of_retail_pct | 13.5 | % of retail turnover (online EUR 92.3bn, net) | Germany | 2025 | B | HDE Online-Monitor 2026 (share as reported by Textilwirtschaft); HDE press release 3 Jun 2026 gives marketplace share 56.7% and FMCG online share 4.9% | [93] |
| London | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Paris | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| Berlin | urban_uplift_factor | not found | ratio metro/national per capita | - | 2025 | C | - |  |
| London | drops_per_vehicle_per_day | 72 | addresses (stops) per van round | central London | 2017 | B | UCL portering study of next-day parcel round (72 addresses, 126 parcels, 7.3 h) | [43] |
| London | shift_hours | 7.3 | hours per van round (72 addresses) | central London | 2017 | B | UCL portering study | [43] |
| London | van_capacity_parcels | 126 | parcels per van round (observed, lower bound of capacity) | central London | 2017 | B | UCL portering study | [43] |
| Paris | drops_per_vehicle_per_day | 70 | stops per vehicle per day (PROXY) | proxy: London van round (72 addresses) | 2025 | C | proxy |  |
| Paris | shift_hours | 8.4 | hours (PROXY) | proxy US vans | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city rounds, 2018 data) | [41] |
| Paris | van_capacity_parcels | 126 | parcels (PROXY) | proxy | 2025 | C | proxy (London van) |  |
| Berlin | drops_per_vehicle_per_day | 126 | stops per courier per working day (one unnamed parcel company; three other firms under 100) | Germany (national, Verdi-linked survey) | 2025 | C | Verkehrsrundschau 25 Nov 2025 on Verdi press conference (survey of couriers) | [115] |
| Berlin | shift_hours | 8.4 | hours (PROXY) | proxy US vans | 2018 | C | Amazon Last Mile Routing Challenge data, analysed in arXiv:2409.06730 (Austin/Boston/Chicago/Seattle in-city rounds, 2018 data) | [41] |
| Berlin | van_capacity_parcels | 206 | parcels delivered per courier per day (same company as 126 stops); observed load | Germany (national, Verdi-linked survey) | 2025 | C | Verkehrsrundschau 25 Nov 2025 | [115] |
| London | cargo_bike_share_pct | not found | % of parcel deliveries | London | 2025 | C | search (Clean Cities/TfL, Ville de Paris, Berlin studies not located with a share) |  |
| Paris | cargo_bike_share_pct | not found | % of parcel deliveries | Paris | 2025 | C | search (Clean Cities/TfL, Ville de Paris, Berlin studies not located with a share) |  |
| Berlin | cargo_bike_share_pct | not found | % of parcel deliveries | Berlin | 2025 | C | search (Clean Cities/TfL, Ville de Paris, Berlin studies not located with a share) |  |
| London | vehicles_per_1000_people | 288 | licensed cars per 1000 residents (all licensed vehicles: 330) | Greater London | 2025 | B | DfT/GLA licensed vehicles by borough (cars 2,630,663 at Dec 2025; light goods 206,503) / ONS mid-2025 population 9.123M | [94] |
| Paris | vehicles_per_1000_people | 575 | passenger cars per 1000 (France national; PROXY) | France | 2025 | C | SDES 39.7M cars in circulation at 1 Jan 2025 / INSEE 69.08M | [103] |
| Paris | car_ownership_households_pct | 31.8 | % households with at least one car (27.9% one car, 3.8% two or more) | Paris | 2022 | A | INSEE census 2022 via Ville de Paris Bilan 2025 deplacements | [104] |
| Berlin | vehicles_per_1000_people | 330 | cars per 1000 residents (start of 2026) | Berlin | 2026 | B | KBA / Destatis via dpa (Nordkurier, 22 Jul 2026); Germany 593 per 1000 | [102] |
| London | fx_local_per_usd | 0.746661 | GBP per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Paris | fx_local_per_usd | 0.891529 | EUR per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| Berlin | fx_local_per_usd | 0.891529 | EUR per USD | country | 2026 | A | ExchangeRate-API open.er-api.com (updated 2026-10-23 00:02 UTC) | [54] |
| London | fuel_gasoline_usd_per_litre | 2.34 | USD/L (Octane-95) | United Kingdom | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [105] |
| London | fuel_diesel_usd_per_litre | 2.67 | USD/L | United Kingdom | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [106] |
| London | vehicle_operating_cost_per_km | not found | - | United Kingdom | 2025 | C | - |  |
| Paris | fuel_gasoline_usd_per_litre | 2.42 | USD/L (Octane-95) | France | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [107] |
| Paris | fuel_diesel_usd_per_litre | 2.64 | USD/L | France | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [108] |
| Paris | vehicle_operating_cost_per_km | not found | - | France | 2025 | C | - |  |
| Berlin | fuel_gasoline_usd_per_litre | 2.39 | USD/L (Octane-95) | Germany | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [109] |
| Berlin | fuel_diesel_usd_per_litre | 2.55 | USD/L | Germany | 2026 | B | GlobalPetrolPrices.com (19 Oct 2026) | [110] |
| Berlin | vehicle_operating_cost_per_km | not found | - | Germany | 2025 | C | - |  |
| London | driver_wage_usd_per_hour | 18.76 | USD/h (GBP 14.01/h) | United Kingdom (DPD delivery-driver postings, national) | 2026 | C | Indeed UK company page, DPD delivery driver average (70 postings) | [111] |
| Paris | driver_wage_usd_per_hour | 15.72 | USD/h (EUR 14.01/h gross = EUR 25,500/yr / 1,820 h) | France (La Poste/Colissimo chauffeur-livreur median) | 2026 | C | Salerya salary guide for chauffeur-livreur (La Poste median EUR 25,500; junior 22,400; senior 27,000) | [112] |
| Berlin | driver_wage_usd_per_hour | 18.78 | USD/h (EUR 16.75/h gross = EUR 34,834/yr / 2,080 h) | Berlin (median Paketzusteller, 40 h/week) | 2026 | C | gehalt.de salary page for Paketzusteller (Berlin median EUR 34,834; Germany EUR 36,126) | [114] |
| London | delivery_fee_usd | 4.21 | USD average revenue per parcel (GBP 3.14 = GBP 13.2bn / 4.2bn parcels) | United Kingdom (all operators) | 2025 | C | Ofcom Post monitoring report 2024-25 (revenue and volume as reproduced in search-result text) | [84] |
| Paris | delivery_fee_usd | 6.04 | USD average revenue per domestic parcel (EUR 5.38 = EUR 6,757M / 1,255M) | France (domestic parcels, all operators) | 2024 | B | ARCEP Observatoire du courrier et du colis 2024 | [86] |
| Berlin | delivery_fee_usd | 4.4 | USD average revenue per B2X parcel (EUR 3.92 = EUR 14.35bn / 3.66bn, 2023) | Germany (B2X parcels, all operators) | 2023 | B | Bundesnetzagentur Parcels Market Report 2024 | [89] |
| London | n_major_carriers | 5 | count (Royal Mail/Parcelforce, Evri incl. DHL eCommerce UK since Sep 2025, DPD, Amazon Logistics, Yodel now InPost) | United Kingdom | 2025 | C | Ofcom 2024-25 (competitors Evri, DHL, Yodel, DPD in C2X); Pegasus Couriers on Evri-DHL eCommerce merger and InPost-Yodel | [85] |
| London | carrier_market_shares | not found | % of parcels | United Kingdom | 2025 | C | Post & Parcel UK parcel market size report 2026 (paywalled, GBP 2,450) | [85] |
| Paris | n_major_carriers | 5 | count (La Poste group incl. Colissimo, Chronopost, DPD via Geopost; Amazon; Mondial Relay/InPost; GLS; Relais Colis) | France | 2024 | C | La Poste CEO via FashionUnited (Dec 2024); ARCEP lists La Poste, Colis Prive, Mondial Relay, Chronopost, DPD | [116] |
| Paris | carrier_market_shares | La Poste about 50%, Amazon 15%, Mondial Relay 14% | % of French B2C parcels | France | 2024 | C | Philippe Wahl (La Poste CEO) via FashionUnited, 6 Dec 2024 | [116] |
| Berlin | n_major_carriers | 6 | count (DHL Paket, Amazon, DPD, GLS, Hermes, UPS; about 98% of parcels) | Germany | 2023 | A | Bundesnetzagentur Parcels Market Report 2024 | [89] |
| Berlin | carrier_market_shares | DHL over 40%; Amazon 15-20% (German edition says 15-25%); DPD, GLS, Hermes, UPS 5-15% each | % of parcel volume | Germany | 2023 | A | Bundesnetzagentur Parcels Market Report 2024 | [89] |
| London | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Paris | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| Berlin | price_elasticity_delivery_demand | not found | - | - | 2025 | C | Literature search | [78] |
| London | zone_charge_congestion_gbp_per_day | 18 | GBP per day (about USD 24.1); 21 if paid after midnight; Mon-Fri 07:00-18:00, weekends and bank holidays 12:00-18:00 | Central London Congestion Charge zone (~8 sq mi) | 2026 | B | Autoexpress (rate rose to GBP 18 from the start of 2026); Drive.co.uk guide | [117] |
| London | zone_charge_ulez_gbp_per_day | 12.5 | GBP per day (about USD 16.7) for non-compliant cars and vans; 24/7 except Christmas Day | all London boroughs (not the M25) | 2026 | B | Drive.co.uk guide to ULEZ and Congestion Charge | [118] |
| Paris | zone_charge | none found; ZTL transit ban and ZFE | - | Paris | 2026 | A | Ville de Paris (ZTL); Mondial.paris on Conseil constitutionnel decision 2026-903 DC; Automobile-Propre on Metropole du Grand Paris ZFE | [119] |
| Paris | delivery_loading_rules | not found for 2025-26; older rules only | - | Paris | 2017 | C | Ville de Paris Montorgueil pedestrian-zone guide (2017) | [122] |
| Berlin | zone_charge | none found; Umweltzone (green sticker) | - | Berlin inside the S-Bahn ring (~88 sq km) | 2026 | B | Berlin Echo (Umweltzone guide, 7 Jul 2026); VisitBerlin | [123] |

## URLs

1. https://www.mta.info/fares-tolls/tolls/congestion-relief-zone/about
2. https://www.cittimagazine.co.uk/news/congestion-reduction/new-york-congestion-pricing-cuts-manhattan-traffic-by-11-in-first-year-as-scheme-raises-more-than-us550m-for-transit-upgrades.html
3. https://www.mos.ru/en/news/item/31338073/
4. https://www.thestatesman.com/cities/caqm-prohibits-entry-of-non-bs-vi-vehicles-registered-outside-delhi-from-nov-1-1503504464.html
5. https://moneylife.in/article/mumbai-traffic-rules-tightened-from-1st-february-heavy-vehicles-barred-in-peak-hours-parking-curbs-enforced/79546.html
6. https://english.ahram.org.eg/News/108069.aspx
7. https://buenosaires.gob.ar/gcaba_historico/infraestructura/logistica-nocturna-en-carriles-exclusivos
8. https://www.tomtom.com/traffic-index/city/new-delhi/
9. https://www.tomtom.com/traffic-index/city/mumbai/
10. https://www.tomtom.com/traffic-index/city/cairo/
11. https://www.tomtom.com/traffic-index/city/buenos-aires/
12. https://www.tomtom.com/traffic-index/city/new-york-ny/
13. https://www.tomtom.com/traffic-index/ranking/
14. https://databoks.katadata.co.id/en/transportation-logistics/statistics/1ec7ee0a6b3c76e/moscow-had-the-worlds-worst-traffic-congestion-in-2020
15. https://themoscowtimes.com/2024/07/03/moscow-traffic-congestion-among-worlds-worst-study-says
16. https://profile.ru/news/cars/moskva-avtomobilnaya-pochti-vstala-probki-dostigli-9-ballov-1797773/
17. https://inrix.com/blog/congestion-up-fatalities-down-what-the-2025-inrix-global-traffic-scorecard-reveals/
18. https://inrix.com/scorecard-city/
19. https://arxiv.org/pdf/1802.09335
20. https://www.fhwa.dot.gov/ohim/hpmsmanl/appn5.cfm
21. https://trid.trb.org/View/2671565
22. https://citygeographics.org/2025/11/19/world-city-population-map-update-with-the-new-world-urbanization-prospects-2025/
23. https://cairoscene.com/Buzz/Egypt-s-Population-Grows-by-500-Thousand-in-Five-Months
24. https://snob.ru/news/mosstat-chislennost-naseleniia-moskvy-dostigla-133-mln-chelovek/
25. https://chequeado.com/el-explicador/censo-2022-como-evoluciono-la-poblacion-de-la-ciudad-y-la-provincia-de-buenos-aires/
26. https://statranker.org/population/u-s-metro-areas-by-population-2026-snapshot-based-on-2025-census-estimates/
27. https://s-media.nyc.gov/agencies/dcp/assets/files/pdf/data-tools/population/population-estimates/new-york-city-population-estimates-and-trends-march-2026.pdf
28. https://yourstory.com/socialstory/2025/06/indias-population-146-billion-fertility-drops
29. https://tass.com/society/1907243/amp
30. https://elheraldo.com.ar/noticias/interes-general/el-indec-informo-que-hay-46044703-habitantes-en-argentina
31. https://www.census.gov/quickfacts/fact/table/NY,US/PST045225
32. https://www.storyboard18.com/how-it-works/indias-express-logistics-market-poised-for-rapid-growth-to-hit-24-29-billion-shipments-by-fy-2030-redseer-report-60997.htm
33. https://www.kenresearch.com/industry-reports/egypt-smart-logistics-and-e-commerce-warehousing-market
34. https://selsup.ru/blog/rynok-e-commerce-v-2025-godu-8-3-mlrd-zakazov-minimalnyj-rost-za-8-let-i-dolya-marketplejsov-81/
35. https://mercado.com.ar/tendencias/comercio-electronico-el-estudio-anual-de-cace-midio-34-033-238-millones-en-2025
36. https://mercado.com.ar/tendencias/cace-el-ecommerce-facturo-35-326-983-millones-en-2025-y-subio-60
37. https://www.pitneybowes.com/us/shipping-index.html
38. https://www.nism.ac.in/blog/indias-online-retail-flywheel-digital-is-becoming-the-default
39. https://www.capitalfm.co.ke/business/2026/02/russias-online-retail-sales-surge-28pc-in-2025
40. https://www.economyinsights.com/p/us-ecommerce-sales-reached-340-2-billion-in-q2-2026
41. https://arxiv.org/pdf/2409.06730
42. https://mapatlas.eu/de/blog/last-mile-delivery
43. https://discovery-pp.ucl.ac.uk/10101730/1/portering_preprint%281%29.pdf
44. https://businesstoday.in/current/economy-politics/how-are-flipkart-amazon-delivery-boys-doing/story/278572.html
45. https://www.shadowfax.in/sfx_fy25/Shadowfax_Annual_Report_FY24-25.pdf
46. https://www.restaurantindia.in/news/restaurant-india-news-zomato-blinkit-earnings-data-sparks-fresh-debate-on-gig-worker-rights.n14877
47. https://www.theweek.in/wire-updates/national/2025/08/24/bom5-mh-vehicles-mumbai.html
48. https://delhiplanning.delhi.gov.in/sites/default/files/Planning/table_12.pdf
49. https://english.ahram.org.eg/NewsContentMulti/566385/Multimedia.aspx
50. https://www.motorbeam.com/?p=323604
51. https://www.autonews.ru/amp/news/67eff3ac9a794785c094f3d5
52. https://www.infobae.com/economia/2025/06/05/un-informe-privado-revela-cuantos-vehiculos-circulan-por-el-pais-y-preocupa-el-envejecimiento-del-parque-automotor/
53. https://usa.streetsblog.org/2023/04/19/komanoff-dissects-new-york-citys-car-baby-boom
54. https://open.er-api.com/v6/latest/USD
55. https://www.globalpetrolprices.com/India/gasoline_prices/
56. https://www.globalpetrolprices.com/India/diesel_prices/
57. https://www.globalpetrolprices.com/Egypt/gasoline_prices/
58. https://www.globalpetrolprices.com/Egypt/diesel_prices/
59. https://www.globalpetrolprices.com/Russia/gasoline_prices/
60. https://www.globalpetrolprices.com/Russia/diesel_prices/
61. https://www.globalpetrolprices.com/Argentina/gasoline_prices/
62. https://www.globalpetrolprices.com/Argentina/diesel_prices/
63. https://www.globalpetrolprices.com/USA/gasoline_prices/
64. https://www.globalpetrolprices.com/USA/diesel_prices/
65. https://newsroom.aaa.com/2025/09/aaa-new-vehicle-costs-drop-to-11577/
66. https://www.onetonline.org/link/localwages/53-3033.00?st=NY
67. https://cairoscene.com/buzz/minimum-wage-for-private-sector-in-egypt-raised-to-egp-7000
68. https://dreamjob.ru/salary/kurer
69. https://www.cronista.com/economia-politica/salario-minimo-vital-y-movil-de-cuanto-es-en-argentina-en-octubre-2026/
70. https://www.delhivery.com/uploads/2025/11/LettertoShareholders_Q2FY26.pdf
71. https://ideliver-hero-preview.amgad-deliver.duckdns.org/en/pricing
72. https://snob.ru/news/171933/
73. https://yo-facturo.com/blog/como-calcular-el-costo-de-envio-de-un-producto-2026/
74. https://www.digitalcommerce360.com/2025/07/01/amazon-closing-parcel-delivery-gap-with-usps/
75. https://www.parcelandpostaltechnologyinternational.com/?p=18266
76. https://www.unisender.com/ru/blog/news/wildberries-i-ozon-obespechivayut-84-posylok-v-onlajn-torgovle/
77. https://www.developargentina.com/blog/logistica-fulfillment-ecommerce-argentina-2025
78. https://arxiv.org/pdf/2301.00666
79. https://www.tomtom.com/traffic-index/city/london/
80. https://www.tomtom.com/traffic-index/city/paris/
81. https://www.tomtom.com/traffic-index/city/berlin/
82. https://inrix.com/press-releases/2025-global-traffic-scorecard-uk/
83. https://inrix.com/press-releases/2025-global-traffic-scorecard-de/
84. https://www.ofcom.org.uk/siteassets/resources/documents/postal-services/monitoring-reports/2024-25/post-monitoring-report---postal-services-in-the-financial-year-2024-25.pdf
85. https://pegasuscouriers.co.uk/2025/07/uk-courier-industry-insights/
86. https://www.arcep.fr/fileadmin/cru-1758786296/user_upload/observatoire/courrier-et-colis/2024/observatoire-courrier-colis-2024_oct2025.pdf
87. https://logistik-heute.de/news/kep-anzahl-der-sendungen-stieg-2025-auf-4-37-milliarden-270354.html
88. https://onlinemarktplatz.de/256955/kep-studie-2025-wachstumskurs/
89. https://data.bundesnetzagentur.de/Bundesnetzagentur/SharedDocs/Mediathek/Berichte/2024/2025_06_10_Paketmarktbericht_2024_FINAL_en.pdf
90. https://www.ons.gov.uk/businessindustryandtrade/retailindustry/timeseries/j4mc/drsi
91. https://www.ecommerce-nation.fr/bilan-ecommerce-2025-196-milliards-baisse-panier-moyen/
92. https://einzelhandel.de/images/presse/Pressekonferenz/2026/onlinemonitor26/PM_HDE-OnlineMonitor.pdf
93. https://www.textilwirtschaft.de/business/news/hde-prognose-2026-so-stark-werden-die-einzelhandelsumsaetze-dieses-jahr-zulegen-254001
94. https://data.london.gov.uk/dataset/licensed-vehicles-type-borough-2l873
95. https://www.nomisweb.co.uk/api/v01/dataset/NM_2002_1.data.csv?geography=2092957699&date=2024,2025&gender=0&c_age=200&measures=20100&select=geography_name,date_name,obs_value
96. https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/bulletins/annualmidyearpopulationestimates/mid2024
97. https://www.insee.fr/fr/statistiques/fichier/7728806/dep75.pdf
98. https://www.cci-paris-idf.fr/sites/default/files/2026-10/Population.pdf
99. https://www.insee.fr/fr/statistiques/5225246
100. https://www.destatis.de/DE/Presse/Pressemitteilungen/2026/06/PD26_203_124.html
101. https://www.statistik-berlin-brandenburg.de/presse/2026/16-einwohnerregisterstatistik
102. https://www.nordkurier.de/wirtschaft/immer-mehr-autos-nur-in-stadtstaaten-werden-es-weniger-4735468
103. https://www.statistiques.developpement-durable.gouv.fr/397-millions-de-voitures-en-circulation-en-france-au-1er-janvier-2025
104. https://cdn.paris.fr/paris/2026/06/03/paris_ra2025-deplacements-6-pages-20-05-copie-IXTS.pdf
105. https://www.globalpetrolprices.com/United-Kingdom/gasoline_prices/
106. https://www.globalpetrolprices.com/United-Kingdom/diesel_prices/
107. https://www.globalpetrolprices.com/France/gasoline_prices/
108. https://www.globalpetrolprices.com/France/diesel_prices/
109. https://www.globalpetrolprices.com/Germany/gasoline_prices/
110. https://www.globalpetrolprices.com/Germany/diesel_prices/
111. https://uk.indeed.com/cmp/Dpd/salaries/Delivery-Driver
112. https://salerya.fr/metiers/transport/chauffeur-livreur/
113. https://wageindicator.org/ai/work/collective-bargaining-agreement/updates/2026/france-minimum-wage-rises-24-may-31-2026/
114. https://www.gehalt.de/beruf/paketzusteller
115. https://www.verkehrsrundschau.de/nachrichten/transport-logistik/arbeitsbedingungen-in-der-kurier-express-und-paketbranche-kep-3739880
116. https://fashionunited.fr/actualite/business/la-poste-premier-operateur-de-colis-aux-particuliers-deurope-joue-gros-pour-noel/2024120636652
117. https://www.autoexpress.co.uk/tips-advice/108908/london-congestion-charge-map-times-exemptions-and-full-details
118. https://drive.co.uk/guides/london-ulez-cost-boundaries-and-congestion-charge-rules
119. https://www.paris.fr/pages/paris-cree-une-zone-apaisee-dans-le-centre-de-la-capitale-20426
120. https://mondial.paris/actualites/auto-pratique/suppression-des-zfe-2026-le-conseil-constitutionnel-stoppe-la-loi-67959.html
121. https://www.automobile-propre.com/articles/la-metropole-du-grand-paris-prolonge-sa-zfe-malgre-la-suppression-du-dispositif-au-niveau-national/
122. https://www.api-site.paris.fr/mairies/public/assets/2017%2F3%2FMontorgueil%20mode%20d%27emploi.pdf
123. https://berlinecho.de/umweltzone-berlin-karte-plakette-strafen-2026/
124. https://www.visitberlin.de/en/berlin-environmental-zone

Exchange rates (2026-10-23): USD/INR 94.90, USD/EGP 55.22, USD/RUB 81.52, USD/ARS 1,527.85, USD/GBP 0.7467, USD/EUR 0.8915 (ExchangeRate-API, https://open.er-api.com/v6/latest/USD; ECB via Frankfurter INR 94.82 on 2026-10-22 as cross-check).
