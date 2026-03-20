import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Tooltip as HelpTooltip } from "./Tooltip";

interface BacktestStats {
  period: string;
  trading_days: number;
  annualized_return_pct: number;
  annualized_risk_pct: number;
  risk_return_ratio: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  total_return_x: number;
  win_rate_pct: number;
}

interface EquityPoint {
  date: string;
  cumulative_return: number;
}

interface BacktestData {
  market_pair_id: string;
  market_pair_name: string;
  stats: BacktestStats;
  equity_curve: EquityPoint[];
}

const DATA_BASE_URL = import.meta.env.VITE_DATA_BASE_URL || "/data";

export function BacktestChart({ pairId }: { pairId: string }) {
  const [data, setData] = useState<BacktestData | null>(null);

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/${pairId}/backtest.json`)
      .then((r) => {
        if (!r.ok) return null;
        return r.json();
      })
      .then(setData)
      .catch(() => setData(null));
  }, [pairId]);

  if (!data) return null;

  const { stats, equity_curve } = data;

  // Downsample for chart performance (show every Nth point)
  const step = Math.max(1, Math.floor(equity_curve.length / 500));
  const chartData = equity_curve.filter((_, i) => i % step === 0 || i === equity_curve.length - 1);

  return (
    <div className="panel backtest-panel">
      <div className="panel-header">
        <span>
          HISTORICAL PERFORMANCE{" "}
          <HelpTooltip text="Out-of-sample backtest results. The strategy buys the top 30% and sells the bottom 30% of sectors each day based on the previous day's US market signal. Returns assume equal-weight positions with no transaction costs." />
        </span>
        <span className="date-label">{stats.period}</span>
      </div>

      <div className="backtest-stats">
        <div className="stat-item">
          <span className="stat-value">{stats.annualized_return_pct}%</span>
          <span className="stat-label">Annual Return</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.sharpe_ratio}</span>
          <span className="stat-label">Sharpe Ratio</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.max_drawdown_pct}%</span>
          <span className="stat-label">Max Drawdown</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.total_return_x}x</span>
          <span className="stat-label">Total Return</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.win_rate_pct}%</span>
          <span className="stat-label">Win Rate</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.risk_return_ratio}</span>
          <span className="stat-label">Return / Risk</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#888", fontSize: 11 }}
            tickFormatter={(d: string) => d.slice(0, 4)}
            interval={Math.floor(chartData.length / 6)}
          />
          <YAxis
            tick={{ fill: "#888", fontSize: 11 }}
            tickFormatter={(v: number) => `${v.toFixed(1)}x`}
          />
          <Tooltip
            contentStyle={{
              background: "#1a1a2e",
              border: "1px solid #333",
              color: "#e0e0e0",
            }}
            formatter={(value) => [`${Number(value).toFixed(2)}x`, "Cumulative"]}
          />
          <Line
            type="monotone"
            dataKey="cumulative_return"
            stroke="#3fb950"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
