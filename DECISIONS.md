## Decisions
- the decision cutoff is 09:00 UTC, because the power auction happens at 9:20 UTC.
- multiple strategies were tried for the planning wind level, as documented below.

## Planning wind level

A day is **covered** if actual wind meets or exceeds that planning level. The mean difference is **actual minus planned**; positive means more wind than planned.

| Method tried | January days covered | Avg allowance (GWh/day) | Mean actual − plan (GWh/day) |
| --- | ---: | ---: | ---: |
| 56-day daily MW error, 75th percentile | 22/31 | 56.0 | +14.0 |
| Current: 21-day daily percentage error, 80th percentile | 24/31 | 57.7 | +15.8 |
| 21-day hourly median error | 9/31 | 23.4 | −18.6 |
| Hourly median allowance × 3 | 26/31 | 70.2 | +28.2 |
| 21-day hourly 80th-percentile error | 26/31 | 65.3 | +23.4 |
| 21-day hourly 90th-percentile error | 28/31 | 93.1 | +51.2 |
| Median plus residual correction | 28/31 | 70.0 | +28.0 |

**Choice:** 
We take the 21-day daily error percentage. Then take the 80th percentile of that distribution. This value will be subracted from the forecasted wind to get the planning wind level.