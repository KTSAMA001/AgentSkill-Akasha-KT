# Structured Research Skill 留档

**标签**：#agent-skills #agent-workflow #llm #reference
**来源**：OpenAI Codex 应用附带技能集（公开 URL 未知；本机技能目录收录，经 DSH 适配）
**收录日期**：2026-09-02
**来源日期**：2026-08-13
**状态**：📘 有效
**可信度**：⭐⭐⭐（厂商附带技能，社区实践）
**适用版本**：DSH skill 目录格式（SKILL.md 含 name/description frontmatter）

### 概要

OpenAI Codex 附带的“结构化研究”方法论 Skill 完整留档（DSH 适配版）：以显式研究契约、来源分层、声明-证据映射、冲突裁决、时效核验与停止规则，产出可追溯证据、可见不确定性的研究结论。将下方代码块保存为技能目录下的 SKILL.md 即可还原成可用 Skill。

### 内容

````markdown
---
name: structured-research
description: Conduct evidence-bounded research with explicit questions, source hierarchy, claim-to-evidence mapping, conflict resolution, freshness checks, uncertainty, and stopping rules. Use when the agent must investigate across multiple sources, compare claims, verify current or authoritative information, prepare a research brief, perform a literature or technical review, or handle requests such as 深度调研、研究、调查、证据核验、资料对比 whose quality depends on traceable evidence.
---

# Structured Research

Produce a decision-useful answer whose claims can be traced to evidence and whose uncertainty is visible. Optimize for evidence quality and coverage of decisive questions, not source count.

## 1. Establish the research contract

Before broad searching, define:

- the exact question or decision to support;
- the intended audience and how the result will be used;
- scope, non-goals, geography, time window, versions, and required freshness;
- the requested output and acceptable depth;
- a stopping rule based on evidence coverage, time, cost, or remaining uncertainty.

Ask the user only when a missing preference or authority boundary would materially change the result and cannot be discovered. Resolve technical facts through read-only investigation first.

Convert a broad topic into a small set of answerable subquestions. Identify which claims would change the final decision; treat those as decisive claims.

## 2. Build an evidence plan

Choose sources deliberately:

1. Start with current local or first-party evidence when the task concerns an existing system, artifact, or organization.
2. Prefer primary sources for what a product, law, study, system, or author actually states.
3. Add independent, high-quality secondary sources for interpretation, comparison, and counterevidence.
4. Use community posts and search snippets as leads, not as final proof of high-impact claims.

For each decisive claim, track:

- source and exact location;
- publication or observation date, version, and applicable context;
- evidence type: direct observation, primary source, secondary source, or inference;
- whether sources are truly independent or repeat the same upstream claim;
- supporting and contradicting evidence;
- current confidence and unresolved uncertainty.

Do not treat a source as current merely because it is accessible now. Verify the date and version relevant to the claim.

## 3. Search broadly, then read selectively

Run a bounded discovery pass to find terminology, candidate sources, competing explanations, and obvious gaps. Split independent source streams across subagents when this improves speed or diversity without creating coordination risk.

Then deep-read the smallest set of sources that can answer the decisive subquestions. Inspect the relevant body text, method, data, code, or artifact rather than relying on titles, summaries, snippets, or other agents' conclusions.

Record query changes and dead ends only when they affect interpretation or prevent duplicated work. Stop expanding the source list when new sources no longer change claims, confidence, or known gaps.

## 4. Test claims instead of collecting quotations

Map every material conclusion to evidence. For each claim:

1. State what the evidence directly establishes.
2. Separate any inference needed to reach the claim.
3. Look for a plausible counterexample, rival interpretation, or disconfirming source.
4. Check whether the evidence applies to the requested population, environment, version, and time.
5. Calibrate wording to confidence; narrow or withdraw claims that outrun the evidence.

When sources conflict, compare directness, freshness, methodology, independence, incentives, and scope. Explain why one source is more probative instead of resolving conflict by vote counting.

Treat absence of evidence as an unresolved gap unless the search method was capable of detecting the expected evidence.

## 5. Synthesize for the decision

Lead with the answer, then provide:

- the decisive findings and their evidence;
- important alternatives or counterevidence;
- assumptions, uncertainty, and applicability limits;
- what is verified current versus historical or memory-derived;
- the smallest next check that would most reduce remaining uncertainty.

Use a claim table only when several claims must be compared repeatedly. A useful compact schema is:

| Claim | Best evidence | Counterevidence or gap | Confidence | Applicability |
|---|---|---|---|---|

Do not pad the report with search chronology. Preserve enough provenance that another agent or the user can reproduce the important checks.

## 6. Completion test

Finish when all decisive subquestions are answered to the required confidence, or when the stopping budget is reached and the remaining gaps are explicit. Before claiming completion, verify that:

- conclusions answer the original question rather than a nearby topic;
- decisive claims have traceable evidence and appropriate freshness;
- source dependence, conflicts, and negative results are visible;
- fact, quotation, inference, and recommendation are not blended together;
- unverified scope and the next discriminating check are stated.
````

### 相关记录

- [Agent Skills 规范](./agent-skills-spec.md) - Agent Skills 开放标准规范
- [Learning Loop Skill 留档](./learning-loop-skill.md) - 学习闭环方法论 Skill
- [Complex Problem Solving Skill 留档](./complex-problem-solving-skill.md) - 复杂问题求解方法论 Skill

### 验证记录

- [2026-09-02] 初次记录，来源：OpenAI Codex 应用附带技能集（本机收录，DSH 适配版全文留档）
