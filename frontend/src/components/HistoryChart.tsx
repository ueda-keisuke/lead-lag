import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { HistoryEntry } from "../types/signal";

interface Props {
  entries: HistoryEntry[];
}

export function HistoryChart({ entries }: Props) {
  if (entries.length === 0) return null;

  const data = entries.map((e) => ({
    date: e.date,
    shock: e.shock_magnitude,
  }));

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <span>SHOCK MAGNITUDE HISTORY</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#888", fontSize: 11 }}
            tickFormatter={(d: string) => d.slice(5)}
          />
          <YAxis tick={{ fill: "#888", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "#1a1a2e",
              border: "1px solid #333",
              color: "#e0e0e0",
            }}
          />
          <Line
            type="monotone"
            dataKey="shock"
            stroke="#4fc3f7"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
