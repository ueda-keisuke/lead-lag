import type { MarketPairInfo } from "../types/signal";

interface Props {
  pairs: MarketPairInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function MarketPairSelector({ pairs, selectedId, onSelect }: Props) {
  return (
    <div className="pair-selector">
      {pairs.map((p) => (
        <button
          key={p.id}
          className={`pair-tab ${selectedId === p.id ? "active" : ""}`}
          onClick={() => onSelect(p.id)}
        >
          {p.name}
        </button>
      ))}
    </div>
  );
}
