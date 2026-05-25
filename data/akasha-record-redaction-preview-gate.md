# 阿卡西记录写入前脱敏预览门禁

**标签**：#tools #knowledge #akasha #credential
**来源**：阿卡西系统治理更新 + OWASP / GitHub / NIST 公开资料交叉参考
**收录日期**：2026-05-25
**来源日期**：2026-05-25
**更新日期**：2026-05-25
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（系统流程已落地，外部资料方向一致）
**适用版本**：AgentSkill-Akasha-KT 2026-05-25+

### 概要

阿卡西记录写入前必须先做敏感信息语义审查，并在记录前预览中向用户说明是否发现敏感信息、发现的类型或位置概览、以及拟采用的脱敏方式。脚本只能作为结构校验或高置信固定模式告警，不能证明记录“不含敏感信息”。

### 内容

#### 背景

阿卡西记录会长期保存到 `data/*.md` 并同步到配套 Web 展示。记录内容一旦进入 Git 历史和索引链路，后续再删除或修复成本明显高于写入前拦截。因此，脱敏应当作为记录流程的前置门禁，而不是写入后的补救步骤。

原有验证层主要覆盖结构质量：元数据、章节、标签、状态、相对路径、资源引用和索引一致性。这类检查适合脚本化，但不足以识别真实项目名、内部资源标识、业务上下文、代码语义、账号、路径、凭据等需要上下文判断的风险。

#### 结论

1. 脱敏审查是语义质量门禁，主入口应放在记录流程和验证流程中。
2. 记录前预览必须说明脱敏审查结果：是否发现、发现的类型或位置概览、处理方式。
3. 发现敏感信息时，应先泛化、替换为占位符、删除或改写为可复用技术结论，再写入正式记录。
4. 用户要求保留敏感信息时，不应写入共享阿卡西数据层。
5. `validate_records.py` 只负责结构和索引一致性；即使脚本返回 0，也不能声明“无敏感信息”。

#### 需要重点审查的信息

- 真实项目名、内部仓库名、分支名、目录结构、本机绝对路径。
- 账号、邮箱、手机号、客户/人员信息、未公开业务上下文。
- token、API key、密码、私钥、凭据文件内容、授权头、连接串。
- 可反推出内部资产、资源命名、项目结构或业务状态的标识符。
- 截图、命令输出、错误日志、参考链接中的查询参数或临时凭据。

#### 预览说明格式

```markdown
脱敏审查：
- 结果：发现 / 未发现需要处理的敏感信息。
- 类型或位置概览：例如内部路径、真实资源名、凭据字段、人员信息。
- 处理方式：泛化、占位符替换、删除、改写为通用技术结论。
- 剩余边界：脚本未命中不代表无敏感信息，已按当前上下文完成语义审查。
```

#### 与脚本校验的边界

脚本可以继续作为结构门禁，例如检查必填字段、固定状态枚举、标签维度、相对引用和 `INDEX.md` 同步。未来如果加入固定模式扫描，也应定位为高置信告警层，而不是脱敏完成证明。

### 关键代码

不涉及。

### 参考链接

- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) - 日志和记录中应考虑排除、屏蔽、清洗或加密敏感信息。
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) - 建议在开发者侧启用 secrets detection，并明确 secrets 不应明文记录。
- [GitHub Docs: Secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/about-secret-scanning) - GitHub 会扫描仓库、issue、PR、discussion 等文本载体中的凭据泄露。
- [NIST Privacy Framework v1.0](https://www.nist.gov/system/files/documents/2020/01/16/NIST%20Privacy%20Framework_V1.0.pdf) - 支持数据最小化、去标识化、tokenization 和选择性披露。
- [阿卡西记录流程](../references/workflows/record.md) - 已加入记录前预览与脱敏说明门禁。
- [阿卡西验证流程](../references/workflows/validate.md) - 已加入敏感信息与脱敏审查类型。
- [阿卡西脚本说明](../references/scripts/README.md) - 已明确脚本不能证明记录不含敏感信息。

### 相关记录

- [阿卡西记录可视化网站](./akasha-visualization-web.md) - 阿卡西记录会同步到 Web 展示，写入前脱敏能降低长期传播风险。
- [使用 git-filter-repo 重写提交历史（清除敏感信息）](./git-filter-repo-rewrite-history.md) - 写入后清理敏感信息的补救手段成本更高，应优先前置拦截。

### 验证记录

- [2026-05-25] 初次记录：基于阿卡西系统治理更新形成。已同步更新记录流程、验证流程和脚本说明，并执行 `validate_records.py` → `regenerate_index.py` → `validate_records.py` 校验通过。
