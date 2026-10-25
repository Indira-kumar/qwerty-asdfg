# Windward

Wind decision support for a Great Britain electricity buyer. The app shows the latest Elexon wind forecast available at **09:00 GMT** on each purchase decision date in **1–31 January 2026**, a historical confidence score and planning wind level, and the observed result after delivery. The final decision on 31 January concerns delivery on 1 February.

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

For each delivery hour, the service selects the latest forecast with `publishTime <= 09:00 GMT` on the previous day's decision date. It averages the two half-hour actual MW values into one hourly actual MW value. On each decision date, it computes the signed daily error rate `(forecast − actual) / forecast` for the **21 preceding completed delivery days**. The daily planning level is `today's forecast × (1 − max(0, 80th percentile of those rates))`. The hourly chart applies the same rule to same-hour rates; its lower line need not sum to the daily level. The 80% is a historical coverage target, not a guarantee. January actual wind exceeded the daily level on 24 of 31 days (77%).

The confidence score is `round(100 × (1 − historical daily MAPE))`, clipped to 0–100, where MAPE is mean absolute percentage error of daily energy over the same 21 prior days. A score of 88/100 means about 12% average daily error in that history; it is **not** an 88% probability of meeting the forecast or planning level. January actuals evaluate the forecast only after delivery and never enter that decision's level or score. The detailed view also reports hourly MAE and bias.

The 21-day percentage method was selected using December 2025 decisions as a pre-January comparison. Against the prior 56-day absolute-error method, both covered 23 of 31 December days, while the new method reduced the average forecast-to-planning buffer from 70.3 to 59.1 GWh. In the retrospective January backtest it covered 24 of 31 days versus 22 of 31; average buffers were 57.7 versus 55.9 GWh. The additional October history in the snapshot makes the December comparison reproducible. The dashboard still shows only January purchase decisions. Without shortage and surplus purchase costs, this is a balanced planning choice rather than a uniquely optimal trading strategy.

Run `cd api && python -m app.services.compare_planning` to reproduce the candidate comparison.

FUELHH/WIND measures wind farms with operational meters on the Great Britain transmission system. [Elexon notes](https://bmrs.elexon.co.uk/generation-by-fuel-type) that its fuel-type outturn excludes embedded generation and wind farms without operational meters. This is a coverage limit, not missing API records: those farms still generate electricity, but their output is absent from this series. The app therefore describes only this metered wind subset. It does not calculate total power to buy because demand, existing contracted supply, and other generation are outside the two permitted feeds.

## Verification and deployment

Run `cd api && python -m unittest discover -s tests` and `cd client && npm run build`. Vercel can deploy this repository as two projects with root directories `api` and `client`; set the client build variable `VITE_API_BASE_URL` to the deployed API origin. The client includes a Vercel SPA rewrite for `/dashboard`. The public app URL will be added after deployment.

AI tools were used to assist with design, implementation, and review. All data transformations and app behavior were checked against the Elexon sources and local tests.
