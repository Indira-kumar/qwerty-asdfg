import { useState } from "react";
import { ArrowRight, ArrowUpRight, ChevronDown } from "lucide-react";
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

function WindScene() {
  const turbines = [
    { x: 144, y: 494, size: 0.67, delay: "-6s" },
    { x: 335, y: 476, size: 0.83, delay: "-11s" },
    { x: 1136, y: 485, size: 0.72, delay: "-8s" },
    { x: 1326, y: 501, size: 0.55, delay: "-17s" },
  ];

  return (
    <svg className="wind-scene" viewBox="0 0 1440 650" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
      <defs>
        <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#2c527a" />
          <stop offset="1" stopColor="#071b34" />
        </linearGradient>
        <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#9fc7ee" stopOpacity=".47" />
          <stop offset="1" stopColor="#9fc7ee" stopOpacity="0" />
        </linearGradient>
      </defs>
      <ellipse cx="720" cy="512" rx="610" ry="112" fill="url(#horizon)" />
      <path d="M0 511C173 500 330 503 468 510c171 8 323-6 469-2 194 6 321 5 503-4v146H0Z" fill="url(#sea)" />
      <path d="M0 516c146 13 278 4 424 12 162 9 345-4 526 3 166 7 327-9 490 2" fill="none" stroke="#8db3dc" strokeOpacity=".27" strokeWidth="2" />
      <path d="M0 557c241-8 381 12 612 4 278-10 516 2 828-6M0 595c247 6 513-11 734 0 209 10 420 0 706 8" fill="none" stroke="#8db3dc" strokeOpacity=".09" strokeWidth="2" />
      {turbines.map(({ x, y, size, delay }) => (
        <g key={x} transform={`translate(${x} ${y}) scale(${size})`} className="scene-turbine">
          <path d="M0 0 0-154" stroke="#dcecff" strokeWidth="4" />
          <path d="M-12 0h24" stroke="#b4cdeb" strokeWidth="4" />
          <g className="scene-rotor" style={{ animationDelay: delay }}>
            <path d="M0-154 2-216 6-221 4-172ZM0-154l52 32 4 7-43-31ZM0-154l-55 34-7 1 47-35Z" fill="#e3f0ff" />
          </g>
          <circle cy="-154" r="5" fill="#f9fcff" />
        </g>
      ))}
    </svg>
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
              ? `At ${hours[selected]}, forecast ${forecast[selected].toFixed(1)} gigawatts, hourly planning level ${downside[selected].toFixed(1)} gigawatts, actual ${actual[selected].toFixed(1)} gigawatts`
              : `At ${hours[selected]}, forecast ${forecast[selected].toFixed(1)} gigawatts and hourly planning level ${downside[selected].toFixed(1)} gigawatts`
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
            Hourly planning level
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
          <span>Planning level</span>
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
      <main>
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="hero-sky" aria-hidden="true" />
          <WindScene />
          <header className="landing-header">
            <Link className="landing-brand" to="/" aria-label="Windward home">
              <WindwardMark />
              <span>windward</span>
            </Link>
            <nav aria-label="Main navigation">
              <a href="#problem">The problem</a>
              <a href="#product">The product</a>
              <Link className="header-dashboard-link" to="/dashboard">
                Explore pilot <ArrowUpRight size={17} strokeWidth={2} />
              </Link>
            </nav>
          </header>
          <div className="hero-copy">
            <p className="hero-context">For the desk buying tomorrow's power</p>
            <h1 id="landing-title">You have to buy power before you know the wind.</h1>
            <p className="hero-lead">
              At 09:00 GMT, see tomorrow's wind forecast, how accurate recent
              forecasts were, and a cautious level to plan against.
            </p>
            <div className="hero-actions">
              <Link className="landing-primary-cta" to="/dashboard">
                Explore the January pilot <ArrowUpRight size={19} />
              </Link>
              <a className="landing-text-link" href="#problem">
                See the buying problem <ArrowRight size={17} />
              </a>
            </div>
          </div>
          <div className="hero-bottom">
            <span>GB metered wind · Elexon data · January 2026 decisions</span>
            <a href="#problem" aria-label="Scroll to the buying problem">
              Scroll to explore <ChevronDown size={18} />
            </a>
          </div>
        </section>
        <section className="landing-problem" id="problem" aria-labelledby="problem-title">
          <div className="problem-heading">
            <span className="section-index">The buying problem</span>
            <h2 id="problem-title">A single wind number can hide the shortfall you need to cover.</h2>
            <p>
              Your consumers will need power tomorrow. Wind generation will only
              be known tomorrow. If the forecast is high and wind underdelivers,
              the gap still has to be served.
            </p>
          </div>
          <div className="problem-sequence" aria-label="Decision sequence">
            <div className="sequence-line" aria-hidden="true" />
            <article>
              <span className="sequence-time">09:00 · decision day</span>
              <h3>Commit with what is known.</h3>
              <p>Use the latest Elexon forecast actually published by the cutoff, not a later revision that makes the decision look easier in hindsight.</p>
            </article>
            <article>
              <span className="sequence-time">Before the purchase</span>
              <h3>Allow for the miss.</h3>
              <p>See a planning wind level from the previous 21 completed delivery days. The daily amount scales with the forecast using past percentage errors.</p>
            </article>
            <article>
              <span className="sequence-time">After delivery</span>
              <h3>Find out what happened.</h3>
              <p>Compare the frozen forecast with metered wind generation. Understand the error without letting tomorrow's actuals into today's decision.</p>
            </article>
          </div>
        </section>
        <section className="landing-product" id="product" aria-labelledby="product-title">
          <div className="product-intro">
            <div>
              <span className="section-index">The buying view</span>
              <h2 id="product-title">See the forecast. Know its track record. Then reveal the outcome.</h2>
            </div>
            <p>
              A point forecast tells you what might arrive. A confidence score
              shows its historical accuracy, while the planning level shows
              how far similar forecasts have overcalled wind.
              Move through the delivery day below, then reveal actual generation.
            </p>
          </div>
          <div className="product-preview">
            <DecisionPreview />
          </div>
        </section>
        <section className="landing-proof" aria-labelledby="proof-title">
          <div className="proof-copy">
            <span className="section-index">The January pilot</span>
            <h2 id="proof-title">Every wind assumption should come with its evidence.</h2>
            <p>
              Explore every purchase decision from 1–31 January 2026. Inspect the
              forecast available at 09:00, the planning level available then,
              and the measured error after delivery.
            </p>
            <Link to="/dashboard">Inspect the decision history <ArrowRight size={18} /></Link>
          </div>
          <div className="proof-figures">
            <div><strong>31</strong><span>decision dates</span></div>
            <div><strong>2.04 <small>GW</small></strong><span>mean absolute hourly error</span></div>
            <div><strong>77%</strong><span>of days at or above the planning level</span></div>
            <p>Measured across 31 delivery days against an 80% historical coverage target. The planning level and confidence score use only prior completed days. Neither guarantees a delivery outcome.</p>
          </div>
        </section>
        <section className="landing-close" aria-labelledby="close-title">
          <div className="close-content">
            <span>Ready to examine the buying decision?</span>
            <h2 id="close-title">Make the wind assumption one you can explain.</h2>
            <p>Start with the January pilot. Select a decision date, inspect each delivery hour, and see how the forecast held up.</p>
            <Link to="/dashboard">Explore the dashboard <ArrowUpRight size={19} /></Link>
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <div className="landing-brand">
          <WindwardMark />
          <span>windward</span>
        </div>
        <p>Windward informs the wind input to a purchase. Total volume still depends on demand, contracts, and other generation.</p>
        <span>GB metered wind · January 2026 pilot</span>
      </footer>
    </div>
  );
}
