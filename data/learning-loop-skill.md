# Learning Loop Skill 留档

**标签**：#agent-skills #agent-workflow #llm #reference
**来源**：OpenAI Codex 应用附带技能集（公开 URL 未知；本机技能目录收录；经 DeepSeek Harness（DSH）适配——适配仅将 frontmatter description 中的 "Codex" 改为 "the agent"，正文未改动）
**收录日期**：2026-09-02
**来源日期**：2026-08-13
**状态**：📘 有效
**可信度**：⭐⭐⭐（厂商附带技能，社区实践）
**适用版本**：DSH（DeepSeek Harness）skill 目录格式（SKILL.md 含 name/description frontmatter）

### 概要

OpenAI Codex 附带的“学习闭环”方法论 Skill 完整留档（DeepSeek Harness（DSH）适配版，适配范围见来源字段）：通过基线尝试、解释、费力提取、分级提示、反馈、变式与迁移检查，把信息接触转化为可观察、可迁移的能力。将下方代码块保存为技能目录下的 SKILL.md 即可还原成可用 Skill。

### 内容

````markdown
---
name: learning-loop
description: Build demonstrable understanding and transferable skill through baseline attempts, explanation, effortful retrieval, graduated hints, feedback, varied practice, counterexamples, and delayed or novel transfer checks. Use when the agent is asked to teach, tutor, explain for mastery, design a study plan, coach practice, prepare for an exam or interview, close a knowledge gap, or handle requests such as 教我、学习、理解、练习、复习、掌握 and verify application rather than recognition.
---

# Learning Loop

Turn information exposure into observable capability. Do not claim learning from a fluent explanation or immediate repetition alone.

## 1. Define the capability

Translate the topic into a demonstrable performance:

- what the learner should be able to explain, recall, decide, create, diagnose, or execute;
- the starting level and prerequisite knowledge;
- the target context and at least one different transfer context;
- acceptable accuracy, independence, speed, or quality;
- the available session length and later review opportunities.

Use a small transfer task as part of the completion standard. If the learner only needs a reference answer, do not force a full teaching loop.

## 2. Establish a baseline

Ask for a short attempt before showing the solution whenever practical. Use a prediction, explanation, worked step, diagnosis, or recall prompt that reveals the learner's current model.

Classify errors before teaching:

- missing fact or vocabulary;
- incorrect mental model;
- procedural step gap;
- failure to select the right method;
- overload, attention, or confidence problem.

Do not infer inability from one ambiguous prompt. Adjust the probe if language, tooling, or context may be masking the actual capability.

## 3. Build a compact mental model

Explain the smallest model that can generate the correct behavior. Connect new ideas to prerequisites, show why the method works, and expose boundary conditions.

Prefer one clear example followed by a contrasting case. Ask the learner to restate the causal logic in their own words, make a prediction, or identify what would change the answer. Correct misconceptions explicitly rather than merely presenting a polished solution.

Avoid giving every edge case before the core model is usable. Add detail only when it resolves an observed gap or is required for transfer.

## 4. Retrieve before reviewing

After instruction, remove or hide the worked answer and require effortful retrieval:

1. Ask for recall or performance without materials.
2. If blocked, give the smallest hint that preserves productive effort.
3. Escalate hints gradually: cue, partial structure, analogous example, then full solution.
4. Ask for another retrieval attempt after feedback.

Use rereading as repair, not as the main evidence of learning. Keep retrieval challenging but plausibly successful; repeated total failure usually means the model or task must be simplified.

## 5. Give actionable feedback

Compare the attempt with the target and identify:

- what was correct and should be retained;
- the first consequential error, not every cosmetic issue at once;
- why the error occurred;
- one concrete correction;
- the next prompt that tests whether the correction transferred.

Make the learner perform the corrected step. Do not substitute encouragement or answer exposure for another attempt.

## 6. Vary and transfer

Use at least one of each when the target warrants mastery:

- a changed example that preserves the underlying principle;
- a counterexample or boundary case where the usual method should not be used;
- a novel task requiring method selection rather than imitation.

Ask the learner to explain similarities and differences. If performance collapses when surface features change, return to the mental model rather than drilling the original item.

When time permits, schedule or perform a delayed retrieval check. If no delayed check is possible, state that retention remains unverified.

## 7. Calibrate mastery and continue

Claim mastery only when the learner can retrieve and apply the capability with limited support in a new or delayed context. Distinguish:

- exposure: has seen the idea;
- recognition: can identify it with cues;
- recall: can reproduce it without cues;
- application: can use it on a similar task;
- transfer: can select and adapt it in a meaningfully different task.

End with a compact learning record: demonstrated level, recurring error pattern, evidence, next retrieval date or task, and the condition that would change the assessment.

If the same error repeats without improvement, stop repeating the explanation. Recheck prerequisites, change representation or example, reduce task size, or test whether the target capability was defined incorrectly.
````

### 相关记录

- [Agent Skills 规范](./agent-skills-spec.md) - Agent Skills 开放标准规范
- [Structured Research Skill 留档](./structured-research-skill.md) - 结构化研究方法论 Skill
- [Complex Problem Solving Skill 留档](./complex-problem-solving-skill.md) - 复杂问题求解方法论 Skill

### 验证记录

- [2026-09-02] 初次记录，来源：OpenAI Codex 应用附带技能集（本机收录，DeepSeek Harness（DSH）适配版全文留档，适配仅改 frontmatter 描述措辞，正文保留原样）
