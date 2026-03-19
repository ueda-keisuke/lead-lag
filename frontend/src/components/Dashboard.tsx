import { useRef, useState } from "react";
import { useIndex, useSignalData, useHistoryData } from "../hooks/useSignalData";
import { MarketPairSelector } from "./MarketPairSelector";
import { ShockIndex } from "./ShockIndex";
import { SectorRanking } from "./SectorRanking";
import { LeaderReturns } from "./LeaderReturns";
import { HistoryChart } from "./HistoryChart";
import { ShareButtons } from "./ShareButtons";
import { SnapshotButton } from "./SnapshotButton";
import { formatDate } from "../lib/format";

export function Dashboard() {
  const { data: index, error: indexError, loading: indexLoading } = useIndex();
  const [selectedPair, setSelectedPair] = useState<string | null>(null);
  const dashboardRef = useRef<HTMLDivElement>(null);

  // Auto-select first pair
  const activePair = selectedPair || index?.market_pairs[0]?.id || null;

  const { data: signal, error: signalError, loading: signalLoading } = useSignalData(activePair);
  const { data: history } = useHistoryData(activePair);

  if (indexLoading) {
    return <div className="loading">Loading market data...</div>;
  }

  if (indexError) {
    return (
      <div className="error-state">
        <h2>GLOBAL MARKET PROPAGATION</h2>
        <p>Unable to load signal data. The batch job may not have run yet.</p>
        <p className="error-detail">{indexError}</p>
      </div>
    );
  }

  if (!index || index.market_pairs.length === 0) {
    return (
      <div className="error-state">
        <h2>GLOBAL MARKET PROPAGATION</h2>
        <p>No market pairs available yet.</p>
      </div>
    );
  }

  const pairName = index.market_pairs.find((p) => p.id === activePair)?.name || "";

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>GLOBAL MARKET PROPAGATION</h1>
          <p className="subtitle">
            Cross-market lead-lag signal based on subspace-regularized PCA
          </p>
        </div>
        <div className="header-right">
          {signal && (
            <>
              <span className="last-updated">
                Signal for {formatDate(signal.signal_date)}
              </span>
              <SnapshotButton
                targetRef={dashboardRef}
                filename={`market-signal-${signal.signal_date}`}
              />
            </>
          )}
        </div>
      </header>

      <MarketPairSelector
        pairs={index.market_pairs}
        selectedId={activePair}
        onSelect={setSelectedPair}
      />

      {signalLoading && <div className="loading">Loading {pairName} signal...</div>}
      {signalError && <div className="error-detail">Error: {signalError}</div>}

      {signal && (
        <div className="signal-content" ref={dashboardRef}>
          <div className="top-row">
            <ShockIndex
              magnitude={signal.propagation_summary.shock_magnitude}
              factorScores={signal.propagation_summary.factor_scores}
              leaderDate={signal.leader_summary.date}
            />
            <LeaderReturns
              returns={signal.leader_summary.sector_returns}
              date={signal.leader_summary.date}
            />
          </div>

          <SectorRanking
            sectors={signal.signal.sectors}
            countryName={pairName.split("→")[1]?.trim() || "Target"}
          />

          {history && <HistoryChart entries={history.entries} />}

          <ShareButtons
            pairId={signal.market_pair_id}
            signalDate={signal.signal_date}
          />

          <div className="about-section">
            <h2>How it works</h2>
            <div className="about-grid">
              <div className="about-item">
                <span className="about-step">1</span>
                <div>
                  <strong>US market closes</strong>
                  <p>
                    Each day, 11 US sector ETFs finish trading. Their returns
                    capture macro shocks, policy news, and sector-level moves.
                  </p>
                </div>
              </div>
              <div className="about-item">
                <span className="about-step">2</span>
                <div>
                  <strong>Extract common factors</strong>
                  <p>
                    Using subspace-regularized PCA, we decompose the joint
                    US + target market correlation structure into a few
                    stable common factors (global risk, country spread,
                    cyclical vs defensive).
                  </p>
                </div>
              </div>
              <div className="about-item">
                <span className="about-step">3</span>
                <div>
                  <strong>Project onto target market</strong>
                  <p>
                    Today&apos;s US sector returns are projected onto these
                    factors and mapped to the target market&apos;s sectors,
                    producing a predicted signal for the next trading day.
                  </p>
                </div>
              </div>
              <div className="about-item">
                <span className="about-step">4</span>
                <div>
                  <strong>Rank sectors</strong>
                  <p>
                    Sectors are ranked by predicted signal strength.
                    Top 30% are marked LONG (expected to outperform),
                    bottom 30% SHORT (expected to underperform).
                  </p>
                </div>
              </div>
            </div>
            <p className="about-note">
              This is not investment advice. Signals are generated for
              educational and research purposes. Past performance does not
              guarantee future results.
            </p>
            <p className="about-paper">
              Based on:{" "}
              <a
                href="https://www.jstage.jst.go.jp/article/jsaisigtwo/2026/FIN-036/2026_76/_pdf/-char/ja"
                target="_blank"
                rel="noopener noreferrer"
              >
                Nakagawa et al. &quot;Lead-lag strategies for Japanese and U.S.
                sectors using subspace regularization PCA&quot;
              </a>{" "}
              (JSAI SIG-FIN-036, 2026)
            </p>
          </div>

          <footer className="signal-footer">
            <span>
              <a
                href="https://github.com/ueda-keisuke/lead-lag"
                target="_blank"
                rel="noopener noreferrer"
              >
                Source code
              </a>
              {" | "}
              Updated daily at 06:30 UTC
              {" | "}
              leadlag.dev
            </span>
          </footer>
        </div>
      )}
    </div>
  );
}
