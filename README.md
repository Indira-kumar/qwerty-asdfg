# Windward

Wind decision support for a Great Britain electricity buyer. The app shows the latest Elexon wind forecast available at **09:00 GMT** on each purchase decision date in **1–31 January 2026**, its historical downside, and the observed result after delivery. The final decision on 31 January concerns delivery on 1 February.

## Run locally

```bash
docker compose up --build
```

Open `http://localhost:8088` for the app and `http://localhost:8000/docs` for the API. Docker is optional: run `uvicorn app.main:app --reload` from `api/` after installing `api/requirements.txt`, and `npm install && npm run dev` from `client/`.

## Project layout

| Path | Purpose |
| --- | --- |
| `client/src/pages/` | Landing page and decision dashboard |
| `client/src/landing.css` | Landing design and motion |
| `client/src/pages/dashboard.css` | Dashboard styles |
| `api/app/adapters/` | External data interface and Elexon implementation |
| `api/app/services/` | Snapshot preparation and risk calculations |
| `api/app/schemas/` | API response models |
| `api/app/routers/` | API endpoints |
| `api/data/january_2026.json` | Reproducible Elexon-derived demo snapshot |
| `api/tests/` | Cutoff, aggregation, and leakage checks |
| `docker-compose.yml` | Local two-service setup |

## Method

The snapshot builder uses only [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) and [FUELHH/WIND](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream). Regenerate it with `cd api && python -m app.services.prepare_data`. The checked-in snapshot keeps the pilot fast and repeatable.

For each delivery hour, the service selects the latest forecast with `publishTime <= 09:00 GMT` on the previous day's decision date. It averages the two half-hour actual MW values into one hourly actual MW value. Historical signed error is `forecast − actual`; positive error means less wind than forecast. The downside floor subtracts the 90th percentile of **overforecast** error for the same hour from the frozen forecast, using the prior 56 completed delivery days. January actuals evaluate the forecast after delivery; they never enter that decision's pre-buy risk estimate. The detailed view reports MAE, bias, and observed downside coverage (89% across 744 January delivery hours). A 90th-percentile historical floor is an empirical planning indicator, not a guaranteed 90% probability for any particular day; hourly errors are correlated.

FUELHH covers metered Great Britain wind, so it is not a complete measure of UK renewable generation. The app does not calculate total power to buy because demand, existing contracted supply, and other generation are outside the two permitted feeds.

## Verification and deployment

Run `cd api && python -m unittest discover -s tests` and `cd client && npm run build`. Vercel can deploy this repository as two projects with root directories `api` and `client`; set the client build variable `VITE_API_BASE_URL` to the deployed API origin. The client includes a Vercel SPA rewrite for `/dashboard`. The public app URL will be added after deployment.

AI tools were used to assist with design, implementation, and review. All data transformations and app behavior were checked against the Elexon sources and local tests.
