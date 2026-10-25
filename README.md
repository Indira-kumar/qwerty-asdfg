# Windward

Windward helps a Great Britain electricity buying desk judge tomorrow's wind before it commits to day-ahead purchases. The pilot covers buying decisions made **1–31 January 2026** using only Elexon's wind forecast and actual-generation feeds.

## Implementation approach

The original HLD is below. Its **09:00 PM**, **56-day**, and snapshot labels predate the final implementation: the app uses a **09:00 GMT** cutoff, **21 completed days** of history, and live Elexon reads.

![Windward architecture diagram](hld.png)

The project has three parts:

- **Data preparation:** The Elexon adapter reads [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) forecast versions and [FUELHH/WIND](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) actuals on each API request. A bounded, one-hour LRU cache reuses requests for the same dataset and day. The builder selects the latest forecast published by 09:00 GMT for each next-day delivery hour and checks coverage.
- **Python API:** FastAPI serves the January overview through the selected decision date and one decision at a time. The service computes past forecast accuracy, a cautious planning wind level, and after-delivery error; response schemas keep those concepts separate.
- **React client:** The landing page explains the buying problem. The dashboard offers a quick decision view, hourly charts, and a detailed retrospective review.

## Decision method

- **Confidence score:** `100 − average daily percentage error`, rounded and capped at 0–100, using the preceding 21 completed delivery days. It describes past accuracy; **88/100 is not an 88% probability** for tomorrow.
- **Planning wind level:** Reduce the day's forecast by the 80th percentile of signed daily percentage errors from those same 21 days, never increasing the forecast. The third dashboard card shows the difference between forecast and planning level. This is an allowance for less wind, **not a guaranteed minimum or a purchase volume**.
- **After delivery:** Compare the forecast with FUELHH/WIND actuals. Delivery-day actuals never enter that day's decision-time score or planning level. The detailed view shows hourly error, bias, and January coverage.

The lookback and error method were chosen using December 2025 decisions. The 21-day percentage method and the earlier 56-day absolute-error method each covered 23 of 31 December days; the former reduced the average planning buffer from 70.3 to 59.1 GWh. In the retrospective January review, the selected method covered 24 of 31 days. Run `cd api && python -m app.services.compare_planning` to reproduce the comparison.

## Alternatives and tradeoffs

- **Live requests vs a fixed snapshot:** The API reads Elexon directly and caches repeated day requests for one hour. Results may change if Elexon revises source data; the response includes its retrieval time.
- **Planning coverage vs purchase optimization:** The 80% historical coverage target is an interpretable risk allowance, not a guarantee. Demand, existing contracts, and the relative costs of buying too much or too little are unavailable, so the app does not prescribe a purchase quantity.
- **Measured wind vs all wind:** [Elexon notes](https://bmrs.elexon.co.uk/generation-by-fuel-type) that fuel-type outturn excludes embedded wind and farms without operational meters. The app measures forecast accuracy only for this covered wind subset.

## Project layout

| Path | Purpose |
| --- | --- |
| `client/src/pages/`, `client/src/landing.css` | Landing page, dashboard, and visual styles |
| `api/app/adapters/` | Source interface and Elexon adapter |
| `api/app/services/` | Snapshot preparation, decision calculations, comparison |
| `api/app/routers/`, `api/app/schemas/` | HTTP routes and response models |
| `api/app/settings.py`, `api/.env.example` | Validated server configuration and defaults |
| `api/tests/` | Cutoff, alignment, calculation, and leakage checks |
| `hld.png`, `docker-compose.yml` | Initial HLD and local deployment |

## Local setup

```bash
docker compose up --build
```

Open the [app](http://localhost:8088) or the [API docs](http://localhost:8000/docs). For a local run without Docker, install `api/requirements.txt` and run `uvicorn app.main:app --reload` from `api/`; run `npm install && npm run dev` from `client/`.

The API needs network access to Elexon. Copy `api/.env.example` to `api/.env` to override server settings, or set the same variables in the deployment environment. The client uses `VITE_API_BASE_URL` from `client/.env.example` when its API is on another origin; leave it empty for the local proxy.

## Verification and deployment

```bash
cd api && python -m unittest discover -s tests
cd client && npm run build
```

The client and API can be deployed as separate Vercel projects using `client/` and `api/` as root directories. Set `VITE_API_BASE_URL` on the client to the API origin. **Live demo URL:** to be added after deployment.

AI tools assisted with the design, implementation, and review. The data logic and outputs were checked against the Elexon feeds and local tests.
