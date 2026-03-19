"""Write signal output to JSON files."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import SignalOutput


def write_latest_signal(signal: SignalOutput, output_dir: Path) -> Path:
    """Write latest.json for a market pair."""
    pair_dir = output_dir / signal.market_pair_id
    pair_dir.mkdir(parents=True, exist_ok=True)

    data = signal.to_dict()
    out_path = pair_dir / "latest.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return out_path


def append_history(signal: SignalOutput, output_dir: Path, max_days: int = 365) -> Path:
    """Append today's signal summary to history.json."""
    pair_dir = output_dir / signal.market_pair_id
    pair_dir.mkdir(parents=True, exist_ok=True)

    history_path = pair_dir / "history.json"

    if history_path.exists():
        with open(history_path) as f:
            history = json.load(f)
    else:
        history = {"market_pair_id": signal.market_pair_id, "entries": []}

    # Build today's entry
    long_sectors = [s for s in signal.sector_signals if s.position == "long"]
    short_sectors = [s for s in signal.sector_signals if s.position == "short"]

    entry = {
        "date": signal.signal_date,
        "shock_magnitude": round(signal.shock_magnitude, 4),
        "factor_scores": {k: round(v, 4) for k, v in signal.factor_scores.items()},
        "top_long": long_sectors[0].name if long_sectors else "",
        "top_short": short_sectors[-1].name if short_sectors else "",
    }

    # Avoid duplicate entries for same date
    history["entries"] = [e for e in history["entries"] if e["date"] != signal.signal_date]
    history["entries"].append(entry)

    # Keep only recent entries
    history["entries"] = history["entries"][-max_days:]

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return history_path


def write_index(
    market_pair_ids: list[dict],
    output_dir: Path,
) -> Path:
    """Write index.json listing all available market pairs."""
    index = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "market_pairs": market_pair_ids,
    }

    out_path = output_dir / "index.json"
    with open(out_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return out_path
