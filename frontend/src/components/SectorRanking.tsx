import type { SectorSignal } from "../types/signal";
import { formatScore, positionColor } from "../lib/format";

interface Props {
  sectors: SectorSignal[];
  countryName: string;
}

export function SectorRanking({ sectors, countryName }: Props) {
  return (
    <div className="panel sector-panel">
      <div className="panel-header">
        <span>{countryName.toUpperCase()} SECTOR SIGNALS</span>
        <span className="date-label">Tomorrow&apos;s Expected Impact</span>
      </div>
      <table className="sector-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Sector</th>
            <th>Signal</th>
            <th>Position</th>
            <th>Bar</th>
          </tr>
        </thead>
        <tbody>
          {sectors.map((s) => {
            const barWidth = Math.min(Math.abs(s.signal_score) * 80, 100);
            return (
              <tr key={s.ticker} className={`position-${s.position}`}>
                <td className="rank-cell">{s.rank}</td>
                <td className="name-cell">{s.name}</td>
                <td
                  className="score-cell"
                  style={{ color: positionColor(s.position) }}
                >
                  {formatScore(s.signal_score)}
                </td>
                <td className="position-cell">
                  <span
                    className="position-badge"
                    style={{
                      background: positionColor(s.position),
                      opacity: s.position === "neutral" ? 0.3 : 0.9,
                    }}
                  >
                    {s.position.toUpperCase()}
                  </span>
                </td>
                <td className="bar-cell">
                  <div
                    className="signal-bar"
                    style={{
                      width: `${barWidth}%`,
                      background: positionColor(s.position),
                    }}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
