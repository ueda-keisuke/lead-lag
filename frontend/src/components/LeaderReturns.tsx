import type { SectorReturn } from "../types/signal";
import { formatPercent } from "../lib/format";
import { Tooltip } from "./Tooltip";

interface Props {
  returns: SectorReturn[];
  date: string;
}

export function LeaderReturns({ returns, date }: Props) {
  const sorted = [...returns].sort((a, b) => b.return_pct - a.return_pct);

  return (
    <div className="panel leader-panel">
      <div className="panel-header">
        <span>
          US SECTOR RETURNS{" "}
          <Tooltip text="Yesterday's close-to-close returns for 11 US sector ETFs. These are the input to the model — the signal below is derived from how these sectors moved." />
        </span>
        <span className="date-label">{date}</span>
      </div>
      <div className="leader-grid">
        {sorted.map((r) => (
          <div key={r.ticker} className="leader-item">
            <span className="leader-name">{r.name}</span>
            <span
              className="leader-return"
              style={{
                color: r.return_pct >= 0 ? "var(--color-long)" : "var(--color-short)",
              }}
            >
              {formatPercent(r.return_pct)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
