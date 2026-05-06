# 电价预测 Agent — program.md (v0.1)

## 研究方向

输出 96/24 时段日前电价 + 实时电价的**联合概率分布**（含 P05/P10/P25/P50/P75/P90/P95）。

基线模型：Chen-Wang (2015) lattice framework with stochastic volatility，
处理电价 fat-tail、波动率聚集与跳跃 — v2.0 §5.2.1 给出了 GBM vs SV
判定流程，必须先跑一遍正态性 + 独立性检验，几乎可以直接断定要用 SV。

可修改范围：

- 特征：负荷预测、新能源出力、机组检修、省间联络线、煤价、温度
- 波动率模型：GARCH、SV、Heston 离散化
- 混合集成权重
- 跳跃过程参数化
- SV 参数估计粒度（省份 × 月份 × 时段段）

## 约束

- 主指标使用 **CRPS** 或 **Pinball Loss**，**严禁使用 RMSE 作为主指标**
- 必须输出联合分布 — 单时段独立分布会损失时序相关性，下游场景生成会出问题
- 结算价延迟由 `rules.settle_price_delay_days` 控制（广东 = 7 天）
- 出清价延迟由 `rules.realtime_node_price_delay_days` 控制（广东 = 4 天）
- 严禁拟合负电价为正常情况；负电价需要单独建模

## 评估协议

1. CRPS（主指标，必须改善 > 1%）
2. Pinball Loss 各分位数（不能任何一个退化）
3. 极端日 CRPS（高温/寒潮/政策异动日，必须单独评估）
4. SV 参数稳定性（参数估计置信区间过宽时触发 Model-D 人工介入）
5. 推理时间（不能超过 60 秒/天）

## 数据划分

由 `walk_forward.py` 自动生成。

## 已知 Reward Hacking 案例

（持续更新）
