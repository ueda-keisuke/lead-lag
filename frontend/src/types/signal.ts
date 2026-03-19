export interface SectorReturn {
  ticker: string;
  name: string;
  return_pct: number;
}

export interface SectorSignal {
  ticker: string;
  name: string;
  signal_score: number;
  position: "long" | "short" | "neutral";
  rank: number;
}

export interface SignalData {
  market_pair_id: string;
  signal_date: string;
  generated_at: string;
  leader_summary: {
    date: string;
    sector_returns: SectorReturn[];
  };
  signal: {
    sectors: SectorSignal[];
    long_count: number;
    short_count: number;
    neutral_count: number;
  };
  propagation_summary: {
    shock_magnitude: number;
    factor_scores: Record<string, number>;
  };
}

export interface HistoryEntry {
  date: string;
  shock_magnitude: number;
  factor_scores: Record<string, number>;
  top_long: string;
  top_short: string;
}

export interface HistoryData {
  market_pair_id: string;
  entries: HistoryEntry[];
}

export interface MarketPairInfo {
  id: string;
  name: string;
  latest_date: string;
}

export interface IndexData {
  last_updated: string;
  market_pairs: MarketPairInfo[];
}
