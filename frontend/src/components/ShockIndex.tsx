import { formatScore } from "../lib/format";

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

export function ShockIndex({ magnitude, factorScores, leaderDate }: Props) {
  const magnitudeClass =
    magnitude > 1.5 ? "shock-high" : magnitude > 0.8 ? "shock-mid" : "shock-low";

  return (
    <div className="panel shock-panel">
      <div className="panel-header">
        <span>US SHOCK INDEX</span>
        <span className="date-label">{leaderDate}</span>
      </div>
      <div className={`shock-value ${magnitudeClass}`}>
        {formatScore(magnitude)}
      </div>
      <div className="factor-scores">
        {Object.entries(factorScores).map(([key, value]) => (
          <div key={key} className="factor-row">
            <span className="factor-name">{FACTOR_LABELS[key] || key}</span>
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
