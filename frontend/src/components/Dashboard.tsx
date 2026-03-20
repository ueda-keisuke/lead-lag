import { useRef, useState } from "react";
import { useIndex, useSignalData, useHistoryData } from "../hooks/useSignalData";
import { MarketPairSelector } from "./MarketPairSelector";
import { ShockIndex } from "./ShockIndex";
import { SectorRanking } from "./SectorRanking";
import { LeaderReturns } from "./LeaderReturns";
import { HistoryChart } from "./HistoryChart";
import { BacktestChart } from "./BacktestChart";
import { ShareButtons } from "./ShareButtons";
import { SignalSummary } from "./SignalSummary";
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

          <SignalSummary
            sectors={signal.signal.sectors}
            countryName={pairName.split("→")[1]?.trim() || "Target"}
          />

          <SectorRanking
            sectors={signal.signal.sectors}
            countryName={pairName.split("→")[1]?.trim() || "Target"}
          />

          {history && <HistoryChart entries={history.entries} />}

          <BacktestChart pairId={signal.market_pair_id} />

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
                  <strong>Rank and trade</strong>
                  <p>
                    Sectors are ranked by signal strength. The paper&apos;s strategy
                    buys the top 30% (LONG) and short-sells the bottom 30% (SHORT)
                    in equal weight. For example, with $10,000: buy $1,000 each of
                    the 5 strongest sectors, and short-sell $1,000 each of the 5
                    weakest. This creates a market-neutral portfolio that profits
                    from relative sector performance regardless of overall market
                    direction.
                  </p>
                </div>
              </div>
            </div>
            <h2>Why this works</h2>
            <div className="about-insight">
              <p>
                Financial data is extremely noisy — daily returns are roughly
                10% signal and 90% noise. Most ML approaches (random forests,
                neural networks, etc.) try to learn patterns from raw data and
                end up fitting the noise.
              </p>
              <p>
                This method takes the opposite approach:{" "}
                <strong>define the structure first, then estimate within it.</strong>
              </p>
              <ul className="about-keys">
                <li>
                  <strong>Structure before estimation</strong> — Instead of
                  letting the model discover patterns freely, we tell it what
                  kinds of patterns to look for: global risk, country spread,
                  and cyclical vs defensive. This eliminates impossible
                  structures before estimation begins.
                </li>
                <li>
                  <strong>Dimensionality reduction via PCA</strong> — 11 US
                  sectors × 17 target sectors = 187 parameters to estimate.
                  PCA compresses this into 3 common factors. Fewer parameters
                  means less overfitting.
                </li>
                <li>
                  <strong>Prior knowledge through regularization</strong> — The
                  model blends data-driven estimates with economic priors
                  (λ=0.9), heavily favoring structure over noise. This is what
                  makes the factors stable day to day.
                </li>
              </ul>
              <p>
                The key insight: in finance,{" "}
                <strong>the right model beats a powerful algorithm.</strong>{" "}
                This is the same philosophy behind the Fama-French factor model —
                define economically meaningful axes, then let the data fill in
                the weights.
              </p>
            </div>

            <p className="about-note">
              This is not investment advice. Signals are generated for
              educational and research purposes. Past performance does not
              guarantee future results. Backtest returns do not include
              transaction costs, bid-ask spreads, or market impact.
              Short-selling sector ETFs may be difficult or unavailable
              for retail investors in some markets.
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
