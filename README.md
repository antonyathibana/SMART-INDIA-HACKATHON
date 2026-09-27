
SIH 2026, Problem Statement 
. A deterministic, non-LLM-first advisory
pipeline for rural MSMEs: real Udyam registration data, real geocoded
locations, real government scheme rules — with an LLM layer used only to
*explain* figures the deterministic backends already computed, never to
invent them.

This file ties the project's modules together at a glance. Each module has
its own README with full setup/usage detail — this is the map, not the
territory.

## Architecture

```
                        ┌─────────────────────────┐
                        │   11-frontend (5173)     │
                        │   React + Vite + Leaflet │
                        └────────────┬─────────────┘
                                     │
                        ┌────────────▼─────────────┐
                        │ 12-integration (8900)     │
                        │ orchestrates 02/03/05/06/07│
                        └──┬────┬────┬────┬────┬────┘
                 ┌─────────┘    │    │    │    └──────────┐
                 ▼              ▼    ▼    ▼                ▼
        02-msme-map-engine  03-market  05-financial  06-scheme  07-opportunity
             (8200)         (8300)      (8100)        (8400)      -risk (8500)
                 │              │                         │            │
                 └──────┬───────┘                         └─────┬──────┘
                        ▼                                       │
              udyam_data_engine (Postgres + PostGIS)             │
              (locations, msme_enterprises, location_coordinates) │
                                                                   │
        09-llm-assistant (8700) ──────────────────────────────────┘
          │  (explains 07's output; grounds every government-fact
          │   sentence through 08; never computes a number itself)
          ├──► 08-government-rag (8600)  — indexed official scheme documents
          └──► 06-scheme-router (8400)   — scheme metadata lookup

        10-multilingual (8800) ──► 09-llm-assistant (8700)
          (translates 09's explanation prose only; every number,
           citation, and source URL passes through untouched)
```

Every arrow is a real HTTP call between independently-deployable FastAPI
services, each with its own directory, `.venv`, `.env`, and (where it has
one) test suite. No module recomputes another's numbers — EMI, loan
amounts, competitor counts, scheme eligibility, and coordinates each have
exactly one deterministic source of truth, and every other module that
displays them copies the value verbatim.

## Modules

Source of truth: `12-integration/app/config.py`'s `SERVICES` dict (the
same table 12-integration's own `/api/integration/health` endpoint reads
from to check every service's liveness).

| Module | Port | Health check | Purpose |
|---|---:|---|---|
| `02-msme-map-engine` | 8200 | `GET /health` | Geographic enumeration + location coordinates |
| `03-market-intelligence` | 8300 | `GET /health` | Local market evidence: enterprises, competitors, category ranking, SWOT |
| `05-financial-engine` | 8100 | `GET /health` | EMI/loan/margin/break-even calculation |
| `06-scheme-router` | 8400 | `GET /health` | Deterministic government scheme eligibility routing |
| `07-opportunity-risk` | 8500 | `GET /health` | Opportunity/risk signal aggregation over 03 + 05 + 06 |
| `08-government-rag` | 8600 | `GET /health` | Grounded government scheme document retrieval (TF-IDF, no LLM) |
| `09-llm-assistant` | 8700 | `GET /health` | Explanation/orchestration layer over 03/05/06/07/08 |
| `10-multilingual` | 8800 | `GET /health` | Translation adapter around 09-llm-assistant (10 languages) |
| `11-frontend` | 5173 | `GET /` | React/Vite web application (map, forms, dashboards) |

`12-integration` (port 8900) is the orchestrator itself — not listed in
its own `SERVICES` dict, since it doesn't call itself. It exposes
`/api/integration/health` (rolls up every service above) and
`/api/integration/analyze` (combines 02/03/05/06/07's real outputs into
one payload, recomputing nothing).

### Supporting modules (not live HTTP services)

- **`01-udyam-data-engine`** (a.k.a. `udyam data engine/`) — the data
  foundation everything else reads from. Loads the raw data.gov.in
  Udyam/MSME CSV dump (36.7M enterprises, all 35 states/UTs) into
  PostgreSQL, builds the `locations`/`msme_enterprises`/`nic_codes`
  reference schema, and exposes `services/queries.py` as the only
  supported read path. Not a running server; other modules query the
  shared database directly (`locations`, `msme_enterprises`, etc.) or, for
  anything geographic, through 02's PostGIS functions.
- **`03-geographic-reconciliation`** — offline batch tooling (not a
  served API) that enriches `location_coordinates` beyond 01's raw data:
  reconciles Udyam's free-text district against the LGD (Local Government
  Directory) hierarchy, then geocodes via Nominatim under a strict,
  auditable acceptance pipeline (state/district conflict checks,
  coordinate-concentration detection, rate-limited, resumable). Every
  coordinate it writes carries real provenance (`source`, `precision`,
  `confidence`) — nothing is fabricated, and nothing is geocoded at a
  coarser precision than it claims.

## Shared database

All modules above (except 11-frontend, which only talks HTTP) connect to
one PostgreSQL + PostGIS database, `udyam_data_engine`, each via its own
`.env` (`PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD`). No module
merges another's schema or bypasses another's API to read data it doesn't
own — 03-market-intelligence and 07-opportunity-risk, for example, query
02's `location_coordinates`/PostGIS functions directly (same database,
read-only), but nothing outside 01 ever writes to `locations` or
`msme_enterprises`.

## Running the whole application locally

```bash
scripts/start-all.sh                # every backend + the frontend
scripts/start-all.sh --no-frontend  # backends only
scripts/stop-all.sh                 # stop everything this script started
```

Safe to re-run: a service already listening on its port is detected and
left alone, never duplicated. Each service loads its own secrets from its
own `.env` — see that module's `.env.example`. Logs land in `logs/<service>.log`.

Once running:
- Frontend: http://localhost:5173
- Integration health (rolls up every service): http://localhost:8900/api/integration/health

## Design principles that hold across every module

- **No fabrication.** A number is either read from the database/config or
  computed by pure arithmetic over numbers that were. Nothing is guessed,
  interpolated, or invented to fill a gap — a gap is reported as a gap.
- **Single source of truth per number.** EMI/loan (05), scheme eligibility
  (06), competitor/enterprise counts (02/03), coordinates (02, enriched by
  03) — every other module that shows one of these copies it verbatim
  from its owning module, never recomputes it.
- **The LLM explains, it doesn't decide.** 09-llm-assistant's guardrail
  verifies every number in its own generated prose against the evidence
  bundle it was given; 10-multilingual translates only that prose, never
  the evidence, citations, or source URLs.
- **Deterministic-first.** 06 (schemes) and 08 (government facts) work
  correctly with zero LLM calls; an LLM is used automatically only where
  configured, never required for the demo's core correctness.

## Known limitations (by design, not hidden)

- Coordinate coverage on `location_coordinates` is partial by construction
  — Udyam registration data has no lat/long field; every coordinate is
  earned through 03's reconciliation pipeline, at whatever pace that
  pipeline has actually run, not backfilled for the sake of a round number.
- 10-multilingual requires a configured translation provider
  (`ANTHROPIC_API_KEY`) for non-English output; without one it returns a
  clear `503`, never an invented translation.
- This is an SIH demo integration, not a production system: no auth layer,
  no production secrets management beyond per-module `.env` files, no
  production observability stack.
# SMART-INDIA-HACKATHON
