import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CalendarDays, Download, Info, Wind } from "lucide-react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./dashboard.css";

type Metrics = {
  mae_mw: number;
  bias_mw: number;
  rmse_mw: number;
  observations: number;
};
type Hour = {
  start_time: string;
  forecast_mw: number;
  downside_mw: number | null;
  upside_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  publish_time: string;
  history_count: number;
};
type Decision = {
  decision_date: string;
  delivery_date: string;
  forecast_mwh: number;
  confidence_score: number | null;
  downside_mwh: number | null;
  actual_mwh: number | null;
  risk: {
    lookback_days: number;
    completed_days: number;
    coverage_target: number;
    planning_error_rate: number | null;
    historical_daily_mape: number | null;
    baseline: Metrics | null;
  };
  realized: Metrics | null;
  hours: Hour[];
};
type Overview = {
  through_date: string;
  days: { decision_date: string; mae_mw: number | null }[];
  heatmap: { decision_date: string; hour: number; error_mw: number | null }[];
  mean_absolute_error_mw: number | null;
  mean_bias_mw: number | null;
  downside_coverage: number | null;
  evaluated_days: number;
  evaluated_hours: number;
};

const API = import.meta.env.VITE_API_BASE_URL ?? "";
const mw = (n: number | null | undefined) =>
  n == null ? "—" : `${Math.round(n).toLocaleString("en-GB")} MW`;
const gwh = (n: number | null | undefined) =>
  n == null ? "—" : `${(n / 1000).toFixed(1)} GWh`;
const dateLabel = (s: string) =>
  new Date(`${s}T12:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
const hourLabel = (s: string) => `${s.slice(11, 13)}:00`;

function WindChart({ hours, actual }: { hours: Hour[]; actual: boolean }) {
  const data = hours.map((h) => ({
    ...h,
    hour: hourLabel(h.start_time),
    band:
      h.downside_mw == null || h.upside_mw == null
        ? null
        : [h.downside_mw, h.upside_mw],
  }));
  return (
    <div
      className="dash-chart"
      role="img"
      aria-label="Hourly forecast, historical uncertainty range and optional actual wind generation"
    >
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart
          data={data}
          margin={{ top: 10, right: 10, left: -22, bottom: 0 }}
        >
          <CartesianGrid
            vertical={false}
            stroke="#e5eaf1"
            strokeDasharray="4 6"
          />
          <XAxis
            dataKey="hour"
            tickLine={false}
            axisLine={false}
            interval={3}
            tick={{ fill: "#61758c", fontSize: 12 }}
            dy={8}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#61758c", fontSize: 12 }}
            tickFormatter={(v) => `${Math.round(v / 1000)}k`}
          />
          <Tooltip
            cursor={{ stroke: "#9aabc0", strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const h = payload[0].payload as Hour;
              return (
                <div className="dash-tooltip">
                  <strong>{hourLabel(h.start_time)} UTC</strong>
                  <span>
                    Forecast <b>{mw(h.forecast_mw)}</b>
                  </span>
                  <span>
                    Hourly planning level <b>{mw(h.downside_mw)}</b>
                  </span>
                  {actual && (
                    <>
                      <span>
                        Actual <b>{mw(h.actual_mw)}</b>
                      </span>
                      <span>
                        Signed error <b>{mw(h.error_mw)}</b>
                      </span>
                    </>
                  )}
                  <small>
                    Published {h.publish_time.slice(11, 16)} UTC ·{" "}
                    {h.history_count} historical hours
                  </small>
                </div>
              );
            }}
          />
          <Area
            dataKey="band"
            type="monotone"
            stroke="none"
            fill="#dde5ff"
            fillOpacity={0.85}
            isAnimationActive={false}
          />
          <Line
            dataKey="forecast_mw"
            type="monotone"
            stroke="#315ce8"
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
          <Line
            dataKey="downside_mw"
            type="monotone"
            stroke="#d98a27"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
            activeDot={false}
            isAnimationActive={false}
          />
          {actual && (
            <Line
              dataKey="actual_mw"
              type="monotone"
              stroke="#078c86"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5 }}
              isAnimationActive={false}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function Heatmap({
  overview,
  selected,
  select,
  actual,
}: {
  overview: Overview;
  selected: string;
  select: (day: string) => void;
  actual: boolean;
}) {
  const lookup = new Map(
    overview.heatmap.map((h) => [`${h.decision_date}:${h.hour}`, h.error_mw]),
  );
  return (
    <div className="dash-heatmap-scroll">
      <div
        className="dash-heatmap"
        role="group"
        aria-label="January hourly forecast errors"
      >
        <div />
        {Array.from({ length: 24 }, (_, h) => (
          <span className="dash-hour-label" key={h}>
            {h % 4 === 0 ? String(h).padStart(2, "0") : ""}
          </span>
        ))}
        {overview.days.map((day) => (
          <div
            className={`dash-heatmap-row ${selected === day.decision_date ? "selected" : ""}`}
            key={day.decision_date}
          >
            <button
              className="dash-day-label"
              onClick={() => select(day.decision_date)}
              aria-label={`Select ${dateLabel(day.decision_date)}`}
            >
              {day.decision_date.slice(8)}
            </button>
            {Array.from({ length: 24 }, (_, h) => {
              const error = actual ? lookup.get(`${day.decision_date}:${h}`) : null;
              const intensity = Math.min(Math.abs(error ?? 0) / 6500, 1);
              const background =
                error == null
                  ? "#edf1f5"
                  : error >= 0
                    ? `rgba(217,138,39,${0.16 + intensity * 0.74})`
                    : `rgba(7,140,134,${0.16 + intensity * 0.74})`;
              return (
                <button
                  key={h}
                  className="dash-heat-cell"
                  style={{ background }}
                  onClick={() => select(day.decision_date)}
                  title={actual
                    ? `${dateLabel(day.decision_date)} ${String(h).padStart(2, "0")}:00 · ${mw(error)}`
                    : `${dateLabel(day.decision_date)} ${String(h).padStart(2, "0")}:00 · actuals hidden`}
                  aria-label={actual
                    ? `${dateLabel(day.decision_date)} ${String(h).padStart(2, "0")}:00, error ${mw(error)}`
                    : `${dateLabel(day.decision_date)} ${String(h).padStart(2, "0")}:00, actuals hidden`}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function ActualToggle({ shown, onToggle }: { shown: boolean; onToggle: () => void }) {
  return (
    <button
      className={`dash-reveal ${shown ? "on" : ""}`}
      aria-pressed={shown}
      onClick={onToggle}
    >
      <span><i /></span>
      {shown ? "Hide actuals" : "Reveal actuals"}
    </button>
  );
}

function exportCsv(d: Decision, actual: boolean) {
  const rows = [
    "start_time,forecast_mw,downside_mw,upside_mw,actual_mw,error_mw,publish_time",
    ...d.hours.map((h) =>
      [
        h.start_time,
        h.forecast_mw,
        h.downside_mw ?? "",
        h.upside_mw ?? "",
        actual ? (h.actual_mw ?? "") : "",
        actual ? (h.error_mw ?? "") : "",
        h.publish_time,
      ].join(","),
    ),
  ];
  const url = URL.createObjectURL(
    new Blob([rows.join("\n")], { type: "text/csv" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = `windward-${d.decision_date}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function DashboardPage() {
  const [selected, select] = useState("2026-01-14");
  const [mode, setMode] = useState<"nutshell" | "detailed">("nutshell");
  const [actual, showActual] = useState(false);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    setOverview(null);
    fetch(`${API}/api/decisions?through=${selected}`, { signal: c.signal })
      .then((r) => {
        if (!r.ok) throw Error("Could not load January overview");
        return r.json();
      })
      .then(setOverview)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => c.abort();
  }, [selected]);
  useEffect(() => {
    const c = new AbortController();
    setDecision(null);
    fetch(`${API}/api/decisions/${selected}`, { signal: c.signal })
      .then((r) => {
        if (!r.ok) throw Error("Could not load the decision");
        return r.json();
      })
      .then((d) => {
        setDecision(d);
        setError("");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => c.abort();
  }, [selected]);
  return (
    <div className="dash-page">
      <header className="dash-header">
        <Link className="dash-logo" to="/">
          <span>
            <Wind size={21} />
          </span>{" "}
          windward<b>.</b>
        </Link>
        <div>Day-ahead wind intelligence</div>
        <Link className="dash-about" to="/">
          About <ArrowRight size={15} />
        </Link>
      </header>
      <main className="dash-main">
        <section className="dash-intro">
          <div>
            <span className="dash-kicker">January 2026 decision review</span>
            <h1>
              Plan for tomorrow's wind
              <br />
              <em>with the risk in view.</em>
            </h1>
            <p>
              See the wind forecast available at 09:00 GMT, a planning level
              based on past errors, and what arrived after delivery.
            </p>
          </div>
          <div className="dash-date-card">
            <span>
              <CalendarDays size={16} /> Buying decision
            </span>
            <label htmlFor="decision-date">Decision date</label>
            <select
              id="decision-date"
              value={selected}
              onChange={(e) => select(e.target.value)}
            >
              {Array.from(
                { length: 31 },
                (_, i) => `2026-01-${String(i + 1).padStart(2, "0")}`,
              ).map((d) => (
                <option key={d} value={d}>
                  {dateLabel(d)}
                </option>
              ))}
            </select>
            <small>
              For delivery{" "}
              {decision
                ? dateLabel(decision.delivery_date)
                : "the following day"}{" "}
              · 09:00 GMT cutoff
            </small>
          </div>
        </section>
        <div className="dash-toolbar">
          <div className="dash-tabs" role="tablist" aria-label="Dashboard view">
            <button
              role="tab"
              aria-selected={mode === "nutshell"}
              className={mode === "nutshell" ? "active" : ""}
              onClick={() => setMode("nutshell")}
            >
              In a nutshell
            </button>
            <button
              role="tab"
              aria-selected={mode === "detailed"}
              className={mode === "detailed" ? "active" : ""}
              onClick={() => setMode("detailed")}
            >
              Detailed analysis
            </button>
          </div>
          <span className="dash-cutoff">
            <i />{" "}
            {actual
              ? "09:00 forecast + after-delivery review"
              : "As known at 09:00 GMT"}
          </span>
        </div>
        {error && (
          <div className="dash-error" role="alert">
            {error}. Check the API service and refresh.
          </div>
        )}
        {!decision && !error && (
          <div className="dash-loading">Loading decision data…</div>
        )}
        {decision && (
          <>
            <section className="dash-metrics" aria-label="Decision summary">
              <article className="dash-metric forecast">
                <span>Expected wind generation</span>
                <strong>{gwh(decision.forecast_mwh)}</strong>
                <div className="dash-confidence">
                  <div className="dash-confidence-heading">
                    <span>Historical accuracy score</span>
                    <b>
                      {decision.confidence_score == null
                        ? "—"
                        : `${decision.confidence_score}/100`}
                    </b>
                  </div>
                  <div
                    className="dash-confidence-track"
                    role="meter"
                    aria-label="Historical accuracy score"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={decision.confidence_score ?? undefined}
                  >
                    <i
                      style={{ width: `${decision.confidence_score ?? 0}%` }}
                    />
                  </div>
                  <small>
                    Previous {decision.risk.completed_days} days: {" "}
                    {decision.risk.historical_daily_mape == null
                      ? "—"
                      : `${Math.round(decision.risk.historical_daily_mape * 100)}%`}{" "}
                    average daily error.
                  </small>
                </div>
              </article>
              <article className="dash-metric primary">
                <span>Planning wind level</span>
                <strong>{gwh(decision.downside_mwh)}</strong>
                <small>
                  A cautious level predicted from the previous {decision.risk.lookback_days} completed days.
                </small>
              </article>
              <article className="dash-metric allowance">
                <span>Allowance for less wind</span>
                <strong>
                  {gwh(
                    decision.downside_mwh == null
                      ? null
                      : Math.max(0, decision.forecast_mwh - decision.downside_mwh),
                  )}
                </strong>
                <small>
                  Expected wind minus planning wind. This is the gap to allow
                  for when sizing purchases.
                </small>
              </article>
            </section>
            <section className="dash-panel">
              <div className="dash-panel-head">
                <div>
                  <span className="dash-kicker">Delivery profile</span>
                  <h2>
                    {mode === "nutshell"
                      ? "The forecast, with room for error."
                      : "Hour-by-hour generation."}
                  </h2>
                  <p>
                    {dateLabel(decision.delivery_date)} · Great Britain ·
                    average MW
                  </p>
                </div>
                <ActualToggle shown={actual} onToggle={() => showActual(!actual)} />
              </div>
              <div className="dash-legend">
                <span>
                  <i className="line blue" /> Forecast
                </span>
                <span>
                  <i className="band" /> Historical error range
                </span>
                <span>
                  <i className="line amber" /> Hourly planning level
                </span>
                {actual && (
                  <span>
                    <i className="line teal" /> Actual
                  </span>
                )}
              </div>
              <WindChart hours={decision.hours} actual={actual} />
              <p className="dash-chart-note">
                <Info size={15} /> The band uses same-hour errors from the
                previous {decision.risk.lookback_days} completed delivery days. The planning level
                uses daily errors.
              </p>
            </section>
            {mode === "nutshell" ? (
              <section className="dash-insights">
                <article className="dark">
                  <span>For the buying desk</span>
                  <h2>Allow for less wind before committing.</h2>
                  <p>
                    Use the planning wind level alongside demand and existing
                    supply to size purchases.
                  </p>
                  <button onClick={() => setMode("detailed")}>
                    Explore the evidence <ArrowRight size={17} />
                  </button>
                </article>
                <article>
                  <span>After delivery</span>
                  <h2>
                    {actual
                      ? gwh(decision.actual_mwh)
                      : "Keep hindsight separate."}
                  </h2>
                  <p>
                    {actual
                      ? `Measured wind on ${dateLabel(decision.delivery_date)}. The forecast missed by ${mw(decision.realized?.mae_mw)} on average.`
                      : "The actual generation is available now, but it was unknown when the 09:00 decision was made."}
                  </p>
                  <button onClick={() => showActual(true)}>
                    Reveal measured outcome <ArrowRight size={17} />
                  </button>
                </article>
              </section>
            ) : (
              <>
                <section className="dash-backtest">
                  <article>
                    <span>Through {dateLabel(selected)}</span>
                    <strong>
                      {!actual || overview?.downside_coverage == null
                        ? "—"
                        : `${Math.round(overview.downside_coverage * 100)}%`}
                    </strong>
                    <h3>Days above the planning level</h3>
                    <p>
                      Observed coverage over {actual ? (overview?.evaluated_days ?? "—") : "—"}{" "}
                      delivery days. The level targets{" "}
                      {Math.round(decision.risk.coverage_target * 100)}%
                      coverage based on prior daily errors; it does not
                      guarantee delivery.
                    </p>
                  </article>
                  <article>
                    <span>Realized accuracy</span>
                    <strong>
                      {!actual || overview?.mean_absolute_error_mw == null
                          ? "—"
                          : `${(overview.mean_absolute_error_mw / 1000).toFixed(2)} GW`}
                    </strong>
                    <h3>Mean absolute error to date</h3>
                    <p>
                      Average absolute gap between the forecast and
                      measured wind.
                    </p>
                  </article>
                  <article>
                    <span>Systematic direction</span>
                    <strong>
                      {!actual || overview?.mean_bias_mw == null
                          ? "—"
                          : `${overview.mean_bias_mw >= 0 ? "+" : ""}${(overview.mean_bias_mw / 1000).toFixed(2)} GW`}
                    </strong>
                    <h3>Forecast bias to date</h3>
                    <p>
                      Positive means forecasts were above actual wind on
                      average.
                    </p>
                  </article>
                </section>
                {overview && (
                  <section className="dash-panel">
                    <div className="dash-panel-head">
                      <div>
                        <span className="dash-kicker">
                          {overview.days.length} {overview.days.length === 1 ? "decision" : "decisions"} × 24 hours
                        </span>
                        <h2>Where the forecast missed.</h2>
                        <p>
                          Each cell is one delivery hour. Select a row to
                          inspect its buying decision.
                        </p>
                      </div>
                      <div className="dash-heat-legend">
                        {actual ? <><i className="teal" /> Underforecast <i className="amber" /> Overforecast</> : "Actual errors hidden"}
                      </div>
                    </div>
                    <Heatmap
                      overview={overview}
                      selected={selected}
                      select={select}
                      actual={actual}
                    />
                  </section>
                )}
                <section className="dash-panel">
                  <div className="dash-panel-head">
                    <div>
                      <span className="dash-kicker">Audit trail</span>
                      <h2>The numbers behind the line.</h2>
                      <p>
                        Forecasts are selected separately for every delivery
                        hour.
                      </p>
                    </div>
                    <div className="dash-audit-actions">
                      <ActualToggle shown={actual} onToggle={() => showActual(!actual)} />
                      <button
                        className="dash-export"
                        onClick={() => exportCsv(decision, actual)}
                      >
                        <Download size={16} /> Export CSV
                      </button>
                    </div>
                  </div>
                  <div className="dash-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Hour UTC</th>
                          <th>Forecast</th>
                          <th>Hourly planning level</th>
                          <th>Actual</th>
                          <th>Signed error</th>
                          <th>Published UTC</th>
                        </tr>
                      </thead>
                      <tbody>
                        {decision.hours.map((h) => (
                          <tr key={h.start_time}>
                            <td>{hourLabel(h.start_time)}</td>
                            <td>{mw(h.forecast_mw)}</td>
                            <td>{mw(h.downside_mw)}</td>
                            <td>{actual ? mw(h.actual_mw) : "—"}</td>
                            <td
                              className={
                                actual && h.error_mw != null && h.error_mw > 0
                                  ? "positive"
                                  : actual ? "negative" : undefined
                              }
                            >
                              {actual ? <>{h.error_mw != null && h.error_mw > 0 ? "+" : ""}{mw(h.error_mw)}</> : "—"}
                            </td>
                            <td>
                              {h.publish_time.slice(0, 16).replace("T", " ")}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}
            <footer className="dash-footer">
              Elexon BMRS · WINDFOR + FUELHH/WIND{" "}
              <span>
                GB transmission-metered wind only; embedded wind is excluded.
                Forecast error = forecast − actual.
              </span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
