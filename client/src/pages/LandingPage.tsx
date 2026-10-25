import { useState } from "react";
import { ArrowRight, ArrowUpRight, MoveRight } from "lucide-react";
import { Link } from "react-router-dom";
import "../landing.css";

const forecast = [
  12.8, 13.4, 14.1, 15.7, 16.2, 15.5, 14.8, 13.9, 13.1, 12.7, 11.9, 11.4, 10.8,
];
const downside = [
  10.6, 11.1, 11.7, 13.1, 13.4, 12.7, 12.1, 11.3, 10.7, 10.3, 9.5, 9.1, 8.6,
];
const actual = [
  12.2, 12.8, 13.5, 14.5, 14.7, 14.2, 13.4, 12.7, 12.3, 11.9, 11.2, 10.7, 10.1,
];
const hours = [
  "00:00",
  "02:00",
  "04:00",
  "06:00",
  "08:00",
  "10:00",
  "12:00",
  "14:00",
  "16:00",
  "18:00",
  "20:00",
  "22:00",
  "24:00",
];
const plot = { left: 42, right: 586, top: 22, bottom: 225 };
const x = (index: number) =>
  plot.left + (index / (forecast.length - 1)) * (plot.right - plot.left);
const y = (value: number) =>
  plot.bottom - ((value - 8) / 10) * (plot.bottom - plot.top);
const line = (values: number[]) =>
  values
    .map((value, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(value)}`)
    .join(" ");
const band = `${line(forecast)} ${downside.map((_, index) => `L ${x(downside.length - 1 - index)} ${y(downside[downside.length - 1 - index])}`).join(" ")} Z`;

function WindwardMark() {
  return (
    <span className="landing-mark" aria-hidden="true">
      <svg viewBox="0 0 42 42" fill="none">
        <path
          d="M5 11h24c4.4 0 6.4-2.4 6.4-5.1M5 20.5h30c3.6 0 5.3 1.9 5.3 4.3S38.5 29 35.2 29M5 30h17.8c4.9 0 7.1 2.2 7.1 6"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

function DecisionPreview() {
  const [showActual, setShowActual] = useState(false);
  const [selected, setSelected] = useState(6);
  const signedError = forecast[selected] - actual[selected];

  return (
    <div
      className="decision-preview"
      aria-label="Illustrative wind decision preview"
    >
      <div className="preview-heading">
        <div>
          <span className="preview-kicker">Decision snapshot</span>
          <h2>Tomorrow's wind, in view.</h2>
        </div>
        <span className="preview-time">
          <span className="preview-time-dot" /> 09:00 GMT
        </span>
      </div>
      <div className="preview-switch" role="group" aria-label="Preview stage">
        <button
          type="button"
          className={!showActual ? "is-active" : ""}
          aria-pressed={!showActual}
          onClick={() => setShowActual(false)}
        >
          Before delivery
        </button>
        <button
          type="button"
          className={showActual ? "is-active" : ""}
          aria-pressed={showActual}
          onClick={() => setShowActual(true)}
        >
          Reveal outcome
        </button>
      </div>
      <div className="preview-chart-wrap">
        <div className="preview-chart-heading">
          <span>Wind generation</span>
          <span>GW</span>
        </div>
        <svg
          className="preview-chart"
          viewBox="0 0 620 260"
          role="img"
          aria-label={
            showActual
              ? `At ${hours[selected]}, forecast ${forecast[selected].toFixed(1)} gigawatts, historical downside ${downside[selected].toFixed(1)} gigawatts, actual ${actual[selected].toFixed(1)} gigawatts`
              : `At ${hours[selected]}, forecast ${forecast[selected].toFixed(1)} gigawatts and historical downside ${downside[selected].toFixed(1)} gigawatts`
          }
        >
          <defs>
            <linearGradient id="landingDownside" x1="0" y1="0" x2="0" y2="1">
              <stop stopColor="#E6A447" stopOpacity=".26" />
              <stop offset="1" stopColor="#E6A447" stopOpacity=".04" />
            </linearGradient>
          </defs>
          {[10, 14, 18].map((value) => (
            <g key={value}>
              <line
                x1={plot.left}
                x2={plot.right}
                y1={y(value)}
                y2={y(value)}
                className="preview-grid-line"
              />
              <text x="6" y={y(value) + 4} className="preview-axis-label">
                {value}
              </text>
            </g>
          ))}
          <path d={band} fill="url(#landingDownside)" />
          <path d={line(downside)} className="preview-downside-line" />
          <path d={line(forecast)} className="preview-forecast-line" />
          <path
            d={line(actual)}
            className={`preview-actual-line ${showActual ? "is-visible" : ""}`}
          />
          <line
            x1={x(selected)}
            x2={x(selected)}
            y1={plot.top}
            y2={plot.bottom}
            className="preview-cursor-line"
          />
          <circle
            cx={x(selected)}
            cy={y(forecast[selected])}
            r="7"
            className="preview-point-halo"
          />
          <circle
            cx={x(selected)}
            cy={y(forecast[selected])}
            r="4"
            className="preview-forecast-point"
          />
          {showActual && (
            <circle
              cx={x(selected)}
              cy={y(actual[selected])}
              r="5"
              className="preview-actual-point"
            />
          )}
          <text x={plot.left} y="251" className="preview-axis-label">
            00:00
          </text>
          <text
            x={x(6)}
            y="251"
            textAnchor="middle"
            className="preview-axis-label"
          >
            12:00
          </text>
          <text
            x={plot.right}
            y="251"
            textAnchor="end"
            className="preview-axis-label"
          >
            24:00
          </text>
        </svg>
        <div className="preview-chart-legend">
          <span>
            <i className="legend-forecast" />
            Forecast
          </span>
          <span>
            <i className="legend-downside" />
            Historical downside
          </span>
          {showActual && (
            <span>
              <i className="legend-actual" />
              Actual
            </span>
          )}
        </div>
      </div>
      <label className="preview-scrubber-label" htmlFor="landing-hour">
        Explore the delivery day <strong>{hours[selected]}</strong>
      </label>
      <input
        id="landing-hour"
        className="preview-scrubber"
        type="range"
        min="0"
        max="12"
        value={selected}
        onChange={(event) => setSelected(Number(event.target.value))}
      />
      <div className="preview-values" aria-live="polite">
        <div>
          <span>Forecast</span>
          <strong>
            {forecast[selected].toFixed(1)} <small>GW</small>
          </strong>
        </div>
        <div>
          <span>Downside view</span>
          <strong>
            {downside[selected].toFixed(1)} <small>GW</small>
          </strong>
        </div>
        {showActual && (
          <div className="preview-outcome">
            <span>
              Actual · {signedError >= 0 ? "overforecast" : "underforecast"}{" "}
              {Math.abs(signedError).toFixed(1)} GW
            </span>
            <strong>
              {actual[selected].toFixed(1)} <small>GW</small>
            </strong>
          </div>
        )}
      </div>
      <p className="preview-disclaimer">
        Illustrative preview. Dashboard figures use Elexon data.
      </p>
    </div>
  );
}

export function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <Link className="landing-brand" to="/" aria-label="Windward home">
          <WindwardMark />
          <span>windward</span>
        </Link>
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <Link className="header-dashboard-link" to="/dashboard">
            Open dashboard <ArrowUpRight size={17} strokeWidth={2} />
          </Link>
        </nav>
      </header>
      <main>
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="hero-copy">
            <div className="hero-context">
              <span className="hero-context-line" /> Wind intelligence for GB
              day-ahead decisions
            </div>
            <h1 id="landing-title">
              Know the wind
              <br />
              before you buy<span className="hero-period">.</span>
            </h1>
            <p>
              See the forecast available at decision time, understand its
              historical downside, and buy with a clearer picture of the risk.
            </p>
            <div className="hero-actions">
              <Link className="landing-primary-cta" to="/dashboard">
                Explore January decisions{" "}
                <ArrowUpRight size={20} strokeWidth={2} />
              </Link>
              <a className="landing-text-link" href="#how-it-works">
                See how it works <ArrowRight size={18} />
              </a>
            </div>
            <div className="hero-footnote">
              <span className="footnote-line" /> Built around Elexon wind
              forecasts and actual generation
            </div>
          </div>
          <div className="hero-visual">
            <DecisionPreview />
          </div>
        </section>
        <section
          className="landing-method"
          id="how-it-works"
          aria-labelledby="method-title"
        >
          <div className="method-intro">
            <p className="section-index">The decision, made clearer</p>
            <h2 id="method-title">
              From a forecast
              <br />
              to a buying view.
            </h2>
            <p>
              Wind moves. Your decision has a deadline. Windward keeps the
              forecast, its uncertainty, and the eventual result in their proper
              order.
            </p>
          </div>
          <div className="method-steps">
            <article>
              <div className="step-top">
                <span
                  className="step-symbol step-symbol-blue"
                  aria-hidden="true"
                >
                  ↗
                </span>
                <span className="step-number">01</span>
              </div>
              <h3>Freeze the right forecast</h3>
              <p>
                See the latest wind forecast published by 09:00 GMT for the next
                delivery day.
              </p>
            </article>
            <article>
              <div className="step-top">
                <span
                  className="step-symbol step-symbol-amber"
                  aria-hidden="true"
                >
                  ≈
                </span>
                <span className="step-number">02</span>
              </div>
              <h3>Make room for error</h3>
              <p>
                Compare it with the misses seen over the previous 56 completed
                delivery days.
              </p>
            </article>
            <article>
              <div className="step-top">
                <span
                  className="step-symbol step-symbol-teal"
                  aria-hidden="true"
                >
                  ✓
                </span>
                <span className="step-number">03</span>
              </div>
              <h3>Learn from the outcome</h3>
              <p>
                After delivery, compare the frozen forecast with actual wind
                generation, hour by hour.
              </p>
            </article>
          </div>
        </section>
        <section className="landing-close" aria-labelledby="close-title">
          <div className="close-grid" aria-hidden="true" />
          <div className="close-content">
            <span>January 2026 decision window</span>
            <h2 id="close-title">
              Every decision has a forecast.
              <br />
              Now it has context.
            </h2>
            <Link to="/dashboard">
              Open the dashboard <MoveRight size={22} />
            </Link>
          </div>
          <div className="close-mark" aria-hidden="true">
            <WindwardMark />
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <div className="landing-brand">
          <WindwardMark />
          <span>windward</span>
        </div>
        <p>Wind forecast intelligence for day-ahead decisions.</p>
        <span>Great Britain · January 2026</span>
      </footer>
    </div>
  );
}
