"""预测层 — 三个独立 Agent，每个 Agent 一份 program.md.

Agents are deliberately decoupled: AutoResearch can rewrite each agent's
training code without touching the other two or the decision layer.
"""
