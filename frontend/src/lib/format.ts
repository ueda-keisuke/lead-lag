export function formatScore(score: number): string {
  const sign = score >= 0 ? "+" : "";
  return `${sign}${score.toFixed(4)}`;
}

export function formatPercent(pct: number): string {
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function scoreColor(score: number): string {
  if (score > 0.01) return "var(--color-long)";
  if (score < -0.01) return "var(--color-short)";
  return "var(--color-neutral)";
}

export function positionColor(position: string): string {
  switch (position) {
    case "long":
      return "var(--color-long)";
    case "short":
      return "var(--color-short)";
    default:
      return "var(--color-neutral)";
  }
}
