"""决策层 — 两阶段随机规划骨架 + 双层 Control-by-Model.

外层（model selector）+ 内层（Robust MDP / FQI-GBM）的双层架构 —
v2.0 §4.4 / §4.5. 骨架冻结，AutoResearch 只能调子组件。
"""
