# Complex Problem Solving Skill 留档

**标签**：#agent-skills #agent-workflow #llm #reference
**来源**：OpenAI Codex 应用附带技能集（公开 URL 未知；本机技能目录收录，经 DSH 适配）
**收录日期**：2026-09-02
**来源日期**：2026-08-13
**状态**：📘 有效
**可信度**：⭐⭐⭐（厂商附带技能，社区实践）
**适用版本**：DSH skill 目录格式（SKILL.md 含 name/description frontmatter）

### 概要

OpenAI Codex 附带的“复杂问题求解”方法论 Skill 完整留档（DSH 适配版）：以系统边界、竞争假设、可证伪预测、信息增益探针与有界恢复，处理多因、跨系统、高代价的诊断与决策问题。将下方代码块保存为技能目录下的 SKILL.md 即可还原成可用 Skill。

### 内容

````markdown
---
name: complex-problem-solving
description: Frame and solve ambiguous, multi-causal, cross-system, or high-consequence problems using system boundaries, dependency maps, competing hypotheses, falsifiable predictions, information-gain probes, decision records, and bounded recovery. Use when the agent must diagnose intermittent failures, choose among architectures or strategies, untangle interacting constraints, make a difficult decision, escape repeated attempts with no new evidence, or handle requests such as 复杂问题、疑难排查、根因分析、方案决策、卡住了.
---

# Complex Problem Solving

Reduce uncertainty before increasing solution complexity. Preserve multiple explanations until evidence distinguishes them, then converge on the smallest effective intervention.

## 1. Frame the real problem

Write a concise problem frame:

- current state and directly observed symptom;
- desired state and observable success criteria;
- gap between them;
- system boundary, affected actors, dependencies, and interfaces;
- constraints, non-goals, authorization, and irreversible actions;
- reproduction conditions, frequency, timeline, and recent changes;
- stopping budget and escalation conditions.

Separate diagnosis from remediation. If only diagnosis is authorized, identify likely causes and tests without changing the system.

Verify that the problem independently exists. Check whether the symptom is stale, measurement-induced, expected behavior, a misunderstanding of the goal, or an artifact of the observation path.

## 2. Build the system and evidence map

Map the minimum causal chain from input to observed outcome. Include state owners, transformations, boundaries, caches, asynchronous steps, external dependencies, and feedback loops that could explain the symptom.

Maintain four categories:

- **facts**: directly observed and reproducible;
- **inferences**: reasoned from facts but not directly observed;
- **assumptions**: temporarily accepted for progress;
- **unknowns**: information whose value may justify a probe.

Mark source, timestamp or version, and applicability for high-impact facts. Do not let a diagram or prior incident replace current evidence.

## 3. Choose the reasoning branch

Use a diagnostic branch when the task asks why an observed outcome occurs. Generate causal hypotheses and discriminate them with probes as described below.

Use a decision branch when the task asks which architecture, strategy, vendor, policy, or intervention to choose:

1. Define the decision objective, hard constraints, and the status-quo option.
2. Separate factual performance criteria from stakeholder preferences. Ask for a missing business preference only when it can change the choice and cannot be inferred safely.
3. Compare at least two viable options across normal, adverse, and growth scenarios. If hard constraints leave only one viable option, record the evidence that eliminates the others. Record uncertainty, dependencies, side effects, and total switching or operating cost.
4. Test sensitivity: identify whether a reasonable change in weights, forecasts, or assumptions changes the preferred option. If it does, investigate that uncertainty before declaring a winner.
5. Prefer staged, reversible pilots when evidence is weak. Raise the evidence and authorization threshold before an irreversible or hard-to-reverse commitment.
6. If one unknown dominates the choice, design the smallest probe that resolves it. If no remaining uncertainty can change the choice, decide and record the reversal conditions.

Do not hide value judgments inside technical scores. Use a compact option matrix only when repeated criteria comparison makes the trade-off clearer than prose.

## 4. Generate competing hypotheses

Create at least two materially different hypotheses when uncertainty is real. Include non-code explanations such as configuration, environment, data, timing, measurement, requirements, permissions, and user workflow.

For each hypothesis, specify:

- causal mechanism;
- observations it predicts;
- observations that would weaken or falsify it;
- affected scope and expected side effects;
- current evidence for and against it;
- cheapest safe discriminating probe.

Avoid vague labels such as “environment issue” or “race condition” unless they imply a concrete mechanism and testable prediction.

## 5. Select the next probe

Rank probes by:

1. information gain: how strongly the result separates hypotheses;
2. safety and reversibility;
3. cost and user waiting time;
4. observability and reproducibility;
5. risk of contaminating the state being measured.

Prefer a probe that can eliminate an entire branch over a large implementation that merely might work. Record the predicted result before running it so hindsight does not rewrite the hypothesis.

Run independent read-only probes in parallel when coordination cost is low. Serialize writes to shared state, and change one causal variable at a time when attribution matters.

## 6. Update and converge

After each probe:

1. Compare prediction with observation.
2. Update confidence in every relevant hypothesis, not only the favored one.
3. Record surprising or negative evidence.
4. Decide whether to gather more information, revise the frame, or exploit the leading explanation.

Converge when one explanation has sufficient evidence for the decision's risk level. Choose the smallest intervention that addresses the causal mechanism, preserves constraints, and can be verified. A temporary mitigation may be appropriate when explicitly authorized and clearly labeled; do not present it as a root-cause fix.

## 7. Verify the intervention

Reproduce the original failure before the change when safe, then verify after the change under the same conditions. Check:

- the target symptom and the user-visible purpose;
- predicted downstream effects;
- regressions and adjacent states;
- whether the result persists across the relevant time, load, restart, or environment boundary;
- whether evidence supports causation rather than coincidence.

Separate requirement verification from validation of the real-world outcome. State any boundary that could not be tested.

## 8. Recover from stalled loops

Stop the current path after two consecutive attempts that add no evidence, or earlier when risk rises. Recheck:

- whether the goal and success criterion are still correct;
- whether the problem still exists and is reproducible;
- whether the system boundary omits a dependency or actor;
- whether evidence came from the wrong layer or observation tool;
- whether all hypotheses share an untested assumption.

Then change at least one dimension: hypothesis, viewpoint, observer, tool, scale, environment, boundary, or experiment design. Do not repeat the same action with cosmetic variation.

When the stopping budget is reached, deliver a blocker report containing verified facts, attempted probes and outcomes, rejected explanations, remaining hypotheses, risks, and the single next action with highest expected information gain.

## 9. Record the decision

For material decisions, capture:

- chosen option and intended outcome;
- alternatives considered and why they lost;
- decisive evidence and remaining assumptions;
- cost, reversibility, and side effects;
- verification result;
- reversal or review conditions.

Keep the record proportional to consequence. The goal is to preserve reasoning that future evidence can challenge, not to produce ceremony.
````

### 相关记录

- [Agent Skills 规范](./agent-skills-spec.md) - Agent Skills 开放标准规范
- [Structured Research Skill 留档](./structured-research-skill.md) - 结构化研究方法论 Skill
- [Learning Loop Skill 留档](./learning-loop-skill.md) - 学习闭环方法论 Skill

### 验证记录

- [2026-09-02] 初次记录，来源：OpenAI Codex 应用附带技能集（本机收录，DSH 适配版全文留档）
