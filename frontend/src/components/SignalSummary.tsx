import type { SectorSignal } from "../types/signal";

interface Props {
  sectors: SectorSignal[];
  countryName: string;
}

export function SignalSummary({ sectors, countryName }: Props) {
  const longs = sectors.filter((s) => s.position === "long");
  const shorts = sectors.filter((s) => s.position === "short");

  return (
    <div className="panel summary-panel">
      <div className="panel-header">
        <span>TOMORROW IN {countryName.toUpperCase()}</span>
      </div>
      <div className="summary-grid">
        <div className="summary-col summary-long">
          <div className="summary-label">Expected to outperform</div>
          {longs.map((s) => (
            <div key={s.ticker} className="summary-sector">{s.name}</div>
          ))}
        </div>
        <div className="summary-col summary-short">
          <div className="summary-label">Expected to underperform</div>
          {shorts.map((s) => (
            <div key={s.ticker} className="summary-sector">{s.name}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
