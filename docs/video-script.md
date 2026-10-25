# Windward video script

Aim for **8–9 minutes total**. Record the client pitch first, then the technical review. Keep each part under five minutes. Use the **8 January 2026** decision for the client demo.

## Part 1 — client pitch (about 4 minutes 20 seconds)

### 0:00–0:40 · The buying problem

**Show:** Landing headline, then scroll into the decision timeline.

> Tomorrow's demand has to be covered before tomorrow's wind is known. A single forecast gives your buying desk a number, but it does not show how much trust to put in it. Windward is a decision view for that exact moment. It keeps the forecast available at your 09:00 GMT cutoff and puts its recent track record beside it.

### 0:40–1:40 · The decision snapshot

**Show:** Open the dashboard and select 8 January 2026. Point to the three figures.

> This is the decision made on 8 January for delivery on the 9th. The Elexon forecast available at 09:00 was **277.5 GWh**. The historical confidence score is **88 out of 100**: recent daily forecasts had about **12% average error**. That is a measure of past accuracy, not an 88% chance of success. The planning wind level is **238.8 GWh**. The **38.7 GWh** difference is wind we allow for being lower than forecast. It is not a direct instruction to buy 38.7 GWh.

### 1:40–2:30 · The delivery profile

**Show:** Hover across the hourly chart and point out the three visual encodings.

> The daily number hides timing. Here you can inspect every delivery hour, hover for the forecast and planning level, and see a range based on comparable errors from earlier days. The forecast shown here is the version the desk could actually have used. We do not swap in a more accurate revision published later.

### 2:30–3:10 · The outcome

**Show:** Toggle **Reveal actuals**.

> Only after delivery do we reveal measured generation. On 9 January, metered wind delivered **258.2 GWh**. It was below the **277.5 GWh** forecast but above the cautious planning level. Actuals are here for review; that day's actuals were never used to set its decision-time score or planning level.

### 3:10–3:50 · The evidence

**Show:** Open **Detailed analysis** and show January coverage and the hourly error heatmap.

> The detailed view tests the method across all 31 January buying decisions. In this retrospective review, actual wind met or exceeded the daily planning level on **24 of 31 delivery days**. The hourly error view shows where the forecast tended to miss, so the desk can challenge assumptions rather than rely on one headline score.

### 3:50–4:20 · Close

**Show:** Return to the summary cards or the landing page close.

> This pilot makes the wind assumption explainable: what was known before buying, what caution the past suggested, and what happened. It covers the metered wind in the two Elexon feeds. To calculate a total purchase quantity, we would next add demand, existing contracts, other supply, and trading costs.

## Part 2 — technical review (about 4 minutes 30 seconds)

### 0:00–0:40 · Architecture

**Show:** README architecture image, then the project tree.

> The system has three pieces: an Elexon data adapter and snapshot builder, a FastAPI decision service, and a React client. The HLD image is the initial sketch; the final implementation uses a **09:00 GMT** cutoff and **21 completed days** of history. The checked-in snapshot keeps the pilot reproducible and makes page loads independent of Elexon availability.

### 0:40–1:35 · Data preparation

**Show:** `api/app/adapters/elexon.py`, then `api/app/services/prepare_data.py`.

> The adapter owns the two external feeds: WINDFOR versions and FUELHH actuals for WIND. Preparation chooses, for each next-day hour, the latest forecast whose publication time is no later than the decision cutoff. FUELHH is half-hourly; the builder averages each pair into an hourly MW value. It validates that every selected delivery day has 24 matching hours. UTC day alignment matters around British Summer Time, so adjacent settlement dates are read where needed.

### 1:35–2:35 · Decision calculations

**Show:** `api/app/services/decision.py`, then the API docs.

> The service uses only the previous 21 completed delivery days. The confidence score is 100 minus historical daily mean absolute percentage error, clipped to 0–100. That is past accuracy, not a probability. For the daily planning level, it takes the 80th percentile of signed percentage forecast errors, floors the allowance at zero, and reduces today's forecast. The hourly chart uses same-hour history, so its line need not add up to the daily figure. Delivery-day actuals enter retrospective metrics only after that decision is fixed.

### 2:35–3:15 · Product interface

**Show:** React page files; briefly use the dashboard tabs.

> The client separates the buying view from hindsight. The summary gives the forecast, score, planning level, and gap in energy units. The detailed tab exposes the hourly profile, error heatmap, and January backtest. Typed response schemas keep the API contract explicit. The landing preview is labelled illustrative.

### 3:15–3:55 · Verification and deployment

**Show:** Test output and `docker-compose.yml`.

> Tests cover the publication cutoff, half-hour to hourly alignment, risk calculation, and prevention of future-data leakage. The TypeScript build checks the client. Docker Compose starts the API and static client locally. For deployment, they can run as separate Vercel projects with the client pointing to the API origin.

### 3:55–4:30 · Tradeoffs

**Show:** README tradeoffs section; end on the dashboard.

> The 21-day percentage method was chosen using December data. Both candidates covered 23 of 31 December days, while this one needed a smaller average planning buffer. It covered 24 of 31 days in the January retrospective review. The method is a risk aid, not a purchase optimizer: we do not have demand or shortage and surplus costs. Elexon's metered wind also excludes embedded farms, so the product states that scope clearly.

Before recording, replace the README's live-demo placeholder with the deployed URL. Check that the public repository, app, and unlisted video each open in a private browser window.
