"""Base strategy registry for QuantDesk."""

from .base import Strategy
from .buy_and_hold import BuyAndHold
from .inverse_vol_blend import InverseVolatilityBlend
from .ma_crossover import MovingAverageCrossover
from .registry import STRATEGY_REGISTRY

__all__ = [
    "Strategy",
    "BuyAndHold",
    "MovingAverageCrossover",
    "InverseVolatilityBlend",
    "STRATEGY_REGISTRY",
]
