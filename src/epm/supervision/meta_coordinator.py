"""元协调 Agent — v2.0 §3.3.7.

Watches for sus combinations across the prediction Agents (e.g. load up +
price down, sudden volatility spike, confidence collapse) and routes to
human review when triggered.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConflictReport:
    triggered: bool
    rule_hits: list[str]
    human_review_required: bool


@dataclass
class MetaCoordinator:
    load_up_threshold: float = 0.05            # 负荷预测同比涨 ≥5%
    price_down_threshold: float = -0.05        # 电价预测同比跌 ≤−5%
    confidence_collapse_threshold: float = 0.3 # 模型信心下限
    volatility_spike_ratio: float = 2.0        # 波动率突变倍数

    def evaluate(
        self,
        load_yoy: float,
        price_yoy: float,
        model_confidence: float,
        volatility_change_ratio: float,
    ) -> ConflictReport:
        hits: list[str] = []
        if load_yoy > self.load_up_threshold and price_yoy < self.price_down_threshold:
            hits.append("load-up-price-down anomaly")
        if model_confidence < self.confidence_collapse_threshold:
            hits.append(f"confidence collapse ({model_confidence:.2f})")
        if volatility_change_ratio > self.volatility_spike_ratio:
            hits.append(f"volatility spike (×{volatility_change_ratio:.2f})")

        return ConflictReport(
            triggered=bool(hits),
            rule_hits=hits,
            human_review_required=bool(hits),
        )
