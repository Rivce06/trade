"""Name-to-class registry for baseline QuantDesk strategies."""

from __future__ import annotations

from strategies.base import Strategy
from strategies.buy_and_hold import BuyAndHold
from strategies.inverse_vol_blend import InverseVolatilityBlend
from strategies.ma_crossover import MovingAverageCrossover

STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    "buy_and_hold": BuyAndHold,
    "ma_crossover": MovingAverageCrossover,
    "inverse_vol_blend": InverseVolatilityBlend,
}
