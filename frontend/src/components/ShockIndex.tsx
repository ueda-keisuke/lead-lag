import { formatScore } from "../lib/format";
import { Tooltip } from "./Tooltip";

interface Props {
  magnitude: number;
  factorScores: Record<string, number>;
  leaderDate: string;
}

const FACTOR_LABELS: Record<string, string> = {
  global: "Global",
  country_spread: "Country Spread",
  cyclical_defensive: "Cyclical / Defensive",
};

const FACTOR_TIPS: Record<string, string> = {
  global:
    "How much the entire US market moved together. A large positive value means broad risk-on; large negative means risk-off.",
  country_spread:
    "Relative strength between the US and the target market. Positive means the US led upward relative to the target.",
  cyclical_defensive:
    "Whether cyclical sectors (tech, materials, industrials) outperformed defensive ones (utilities, healthcare, staples).",
};

export function ShockIndex({ magnitude, factorScores, leaderDate }: Props) {
  const magnitudeClass =
    magnitude > 1.5 ? "shock-high" : magnitude > 0.8 ? "shock-mid" : "shock-low";

  let regime: string;
  let regimeClass: string;
  if (magnitude > 2.0) {
    regime = "STRONG SHOCK";
    regimeClass = "regime-off";
  } else if (magnitude > 1.0) {
    regime = "MODERATE";
    regimeClass = "regime-mid";
  } else {
    regime = "CALM";
    regimeClass = "regime-on";
  }

  return (
    <div className="panel shock-panel">
      <div className="panel-header">
        <span>
          US SHOCK INDEX{" "}
          <Tooltip text="How strongly the US market moved yesterday. Higher values mean a bigger shock that is more likely to propagate to other markets." />
        </span>
        <span className="date-label">{leaderDate}</span>
      </div>
      <div className="shock-row">
        <div className={`shock-value ${magnitudeClass}`}>
          {formatScore(magnitude)}
        </div>
        <div className={`regime-label ${regimeClass}`}>{regime}</div>
      </div>
      <div className="factor-scores">
        {Object.entries(factorScores).map(([key, value]) => (
          <div key={key} className="factor-row">
            <span className="factor-name">
              {FACTOR_LABELS[key] || key}{" "}
              {FACTOR_TIPS[key] && <Tooltip text={FACTOR_TIPS[key]} />}
            </span>
            <span
              className="factor-value"
              style={{ color: value >= 0 ? "var(--color-long)" : "var(--color-short)" }}
            >
              {formatScore(value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
