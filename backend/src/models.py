"""Data models for market pair config and signal output."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SectorConfig:
    ticker: str
    name: str
    cyclical: bool


@dataclass
class MarketSideConfig:
    country: str
    return_type: str  # "close_to_close" or "open_to_close"
    sectors: list[SectorConfig]

    @property
    def tickers(self) -> list[str]:
        return [s.ticker for s in self.sectors]

    @property
    def cyclical_flags(self) -> list[bool]:
        return [s.cyclical for s in self.sectors]


@dataclass
class AlgorithmParams:
    rolling_window_L: int = 60
    lambda_reg: float = 0.9
    top_K: int = 3
    quantile_q: float = 0.3
    prior_window_start: str = "2010-01-01"
    prior_window_end: str = "2014-12-31"


@dataclass
class MarketPairConfig:
    id: str
    name: str
    leader: MarketSideConfig
    follower: MarketSideConfig


@dataclass
class SectorSignal:
    ticker: str
    name: str
    signal_score: float
    position: str  # "long", "short", "neutral"
    rank: int


@dataclass
class SignalOutput:
    market_pair_id: str
    signal_date: str
    generated_at: str
    leader_date: str
    leader_returns: list[dict]
    sector_signals: list[SectorSignal]
    factor_scores: dict[str, float]
    shock_magnitude: float

    def to_dict(self) -> dict:
        return {
            "market_pair_id": self.market_pair_id,
            "signal_date": self.signal_date,
            "generated_at": self.generated_at,
            "leader_summary": {
                "date": self.leader_date,
                "sector_returns": self.leader_returns,
            },
            "signal": {
                "sectors": [
                    {
                        "ticker": s.ticker,
                        "name": s.name,
                        "signal_score": round(s.signal_score, 4),
                        "position": s.position,
                        "rank": s.rank,
                    }
                    for s in self.sector_signals
                ],
                "long_count": sum(1 for s in self.sector_signals if s.position == "long"),
                "short_count": sum(1 for s in self.sector_signals if s.position == "short"),
                "neutral_count": sum(1 for s in self.sector_signals if s.position == "neutral"),
            },
            "propagation_summary": {
                "shock_magnitude": round(self.shock_magnitude, 4),
                "factor_scores": {k: round(v, 4) for k, v in self.factor_scores.items()},
            },
        }


def load_config(config_path: str | Path) -> tuple[AlgorithmParams, list[MarketPairConfig]]:
    """Load market pair configurations from YAML."""
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    params_raw = raw["parameters"]
    params = AlgorithmParams(
        rolling_window_L=params_raw["rolling_window_L"],
        lambda_reg=params_raw["lambda"],
        top_K=params_raw["top_K"],
        quantile_q=params_raw["quantile_q"],
        prior_window_start=params_raw["prior_subspace_full_window"]["start"],
        prior_window_end=params_raw["prior_subspace_full_window"]["end"],
    )

    pairs = []
    for pair_id, pair_raw in raw["market_pairs"].items():
        leader = MarketSideConfig(
            country=pair_raw["leader"]["country"],
            return_type=pair_raw["leader"]["return_type"],
            sectors=[SectorConfig(**s) for s in pair_raw["leader"]["sectors"]],
        )
        follower = MarketSideConfig(
            country=pair_raw["follower"]["country"],
            return_type=pair_raw["follower"]["return_type"],
            sectors=[SectorConfig(**s) for s in pair_raw["follower"]["sectors"]],
        )
        pairs.append(MarketPairConfig(id=pair_id, name=pair_raw["name"], leader=leader, follower=follower))

    return params, pairs
