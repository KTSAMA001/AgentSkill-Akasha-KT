# Scripts README

本目录存放阿卡西记录的维护脚本。

## 设计原则

- `data/` 是正式知识源，脚本不得擅自修改记录正文语义。
- 索引生成与结构校验分离：一个负责派生输出，一个负责发现问题。
- 校验脚本优先做只读检查，避免为了“修快点”破坏 Web 契约。
- 结构校验与索引同步必须走脚本；禁止把人工抽查、零散 grep 或主观判断当成正式验收流程。

## 脚本列表

### regenerate_index.py

用途：
- 重新生成 `references/INDEX.md` 中的“文件清单”表格。
- 从记录中提取标题、标签、状态和概要，用于派生索引行。

特点：
- 仅重建“文件清单”表格，不会覆盖 `INDEX.md` 其他内容。
- 会输出基础告警，例如缺少标签、缺少状态、缺少概要、未知状态标记。

示例：

```bash
python references/scripts/regenerate_index.py
```

### validate_records.py

用途：
- 对阿卡西正式记录做只读 lint/validate 检查。

当前检查项：
- 文件名是否符合 `kebab-case`
- 必填元数据字段是否存在：标签、来源、收录日期、状态、可信度
- 必填章节是否存在：`### 概要`、`### 验证记录`
- 标签是否已注册，且是否满足“至少 1 个 domain + 恰好 1 个 type”
- 状态是否属于固定枚举
- Markdown 相对引用是否存在，是否误用了绝对路径
- `INDEX.md` 文件清单是否与当前记录内容保持同步

退出码：
- `0`：没有 error
- `1`：存在 error

示例：

```bash
python references/scripts/validate_records.py
python references/scripts/validate_records.py --max-issues 200
```

### fix_records_structure.py

用途：
- 对历史记录执行一次性结构迁移修复。
- 仅补齐模板硬约束，例如必填章节、固定状态枚举、少量可确定元数据、已知失效内部引用与标签归一。

使用边界：
- 该脚本只用于受控整改或批量迁移，禁止把它当成日常录入流程的一部分。
- 该脚本不会替代人工判断，不会为未知语义自动编造结论。
- 执行后必须重新运行 `validate_records.py` 和 `regenerate_index.py` 完成闭环。

示例：

```bash
python references/scripts/fix_records_structure.py
python references/scripts/regenerate_index.py
python references/scripts/validate_records.py
```

## 推荐工作流

以下流程不是建议，而是默认执行基线：

1. 修改或新增记录后，先运行校验脚本。
2. 若校验通过，再按需运行索引重建脚本。
3. 重建后再次运行校验脚本，确认 `INDEX.md` 已同步。

```bash
python references/scripts/validate_records.py
python references/scripts/regenerate_index.py
python references/scripts/validate_records.py
```

## 当前边界

- 这些脚本不会自动修复正文语义问题。
- `fix_records_structure.py` 只会执行受控的结构补齐，不会替代人工做正文语义判断。
- 若要调整模板、workflow、schema 或其他系统规则，应先走治理流程，而不是靠脚本绕过规则。
- 脚本返回报错时，禁止直接忽略并宣称“整体无问题”；必须先解释错误来源，再决定修复或治理动作。