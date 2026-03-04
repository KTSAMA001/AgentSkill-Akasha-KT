# 使用示例合集

> 经验记录系统使用示例集合

---

## 一、查找已有经验

### 示例 1：Unity 协程问题

**用户**："Unity 协程怎么正确等待一帧？"

**操作**：
1. 判断为“查找”意图 → 先读取 `./workflows/search.md`
2. 在 `data/` 目录下执行本地检索（按关键词“协程”“yield”搜索）
3. 命中后读取对应 `data/*.md` 记录并检查状态/适用版本
4. 反馈："在经验记录中找到相关内容，建议使用 `yield return null` 替代 `yield return 0`"

---

### 示例 2：网络搜索

**用户**："Unity DOTS 的 IJobEntity 怎么用？"

**操作**：
1. 判断为“查找”意图 → 先读取 `./workflows/search.md`
2. 在 `data/` 目录下执行本地检索，搜索关键词"DOTS"、"IJobEntity"、"Job"
3. 未找到相关记录 → 告知用户："未在记录中找到，正在上网搜索..."
4. 按优先级搜索 Unity 官方文档与官方论坛
5. 整理搜索结果并展示解决方案
6. 询问："问题解决了吗？需要将此经验记录下来吗？"

---

## 二、记录新经验

### 示例 3：记录 Unity 协程优化

**用户**："帮我记录一下刚才解决的 Unity 协程问题"

**操作**：
1. 识别为“记录”意图 → 先读取 `./workflows/record.md`
2. 按流程执行 `git pull origin main` 拉取仓库最新内容
3. 执行重复检测与正确性验证（参考 `./workflows/validate.md`）
4. 确定文件名为 `unity-coroutine-yield-return-null.md`，写入 `../data/unity-coroutine-yield-return-null.md`
5. 提取关键信息：
   - 标题：Unity 协程优化
   - 问题：协程中使用 yield return 0 导致性能问题
   - 解决：使用 yield return null 更高效
6. 按模板补全标签（至少 2 个）与元数据
7. 同步更新 `./INDEX.md` 文件清单
8. 执行 `git add . && git commit -m "docs: add unity-coroutine-yield-return-null.md" && git push origin main`
9. 反馈："已完成记录并更新索引，且已同步到远程仓库"

---

## 三、更新已有经验

### 示例 4：补充协程注意事项

**用户**："刚才那个协程问题，我发现还有个注意点要补充"

**操作**：
1. 识别为“记录/更新”意图 → 先读取 `./workflows/record.md`
2. 按流程执行 `git pull origin main` 拉取仓库最新内容
3. 定位到 `../data/unity-coroutine-yield-return-null.md` 相关记录
4. 先执行验证检查，再添加更新日期与新增内容
5. 如状态或标签发生变化，同步更新 `./INDEX.md`
6. 执行 `git add . && git commit -m "docs: update unity-coroutine-yield-return-null.md" && git push origin main`

---

## 四、大型架构文档

### 示例 5：保存 VR 变体收集器架构

**用户**："把这个 VR 变体收集器的完整设计文档保存下来"

**操作**：
1. 识别为“记录”意图，读取 `./workflows/record.md`
2. 按流程执行 `git pull origin main`
3. 执行重复检测与正确性验证
4. 创建独立文档：`../data/vr-variant-collector-architecture.md`
5. 编写完整架构设计、打包策略、编译坑点
6. 在 `../data/unity-shader-variants-tool.md` 中追加关联记录：
   - 标题：VR Shader 变体收集器架构
   - 内容：摘要核心的打包策略和优化点
   - 链接：`- [完整架构文档](./vr-variant-collector-architecture.md)`
7. 更新 `./INDEX.md` 文件清单
8. 执行 `git add . && git commit -m "docs: add vr-variant-collector-architecture.md" && git push origin main`

---

## 五、错误经验处理

### 示例 6：WWW 类废弃

**用户**："这个 WWW 类的用法是不是过时了？"

**操作**：
1. 识别为“修正/反馈”意图 → 先读取 `./workflows/validate.md`
2. 执行 `git pull origin main`
3. 搜索 Unity 官方文档确认 WWW 已在 Unity 2018.3 后被标记为 Obsolete
4. 定位对应 `data/*.md` 记录并执行废弃流程：
   - 在原记录标题后添加 `[已废弃]` 标记
   - 状态改为 📕 已过时
   - 在开头添加废弃警告
   - 添加替代方案：推荐使用 UnityWebRequest
5. 添加验证记录并更新 `./INDEX.md`
6. 执行 `git add . && git commit -m "fix: deprecate www usage record" && git push origin main`

**废弃格式**：

```markdown
## [标题] [已废弃]

> ⚠️ **此经验已废弃**
> 废弃原因：Unity 2018.3+ 应使用 UnityWebRequest 替代
> 替代方案：参见 [官方文档](URL)
```

---

## 六、经验冲突处理

### 示例 7：async vs 协程

**用户**："我发现有两个地方说的不一样，一个说用 async/await 好，一个说用协程好"

**操作**：
1. 识别为“修正/反馈”意图 → 先读取 `./workflows/validate.md`
2. 执行 `git pull origin main`
3. 分析冲突原因：这是适用场景不同，不是正确性问题
4. 在两条经验中添加"相关经验"链接，互相引用
5. 明确标注各自的适用条件：
   - **async/await**：适用于纯计算、文件 IO、网络请求等不依赖 Unity 主线程
   - **协程**：适用于等待帧、物理更新、UnityWebRequest 等 Unity 特有异步
6. 添加备注说明选择依据，并更新 `./INDEX.md`（若状态/标签变化）
7. 执行 `git add . && git commit -m "docs: clarify async-vs-coroutine scenarios" && git push origin main`

---

## 七、用户反馈处理

### 示例 8：经验验证失败

**用户**："你之前记录的那个 Unity 协程用 yield return 0 的说法好像不对，我试了报错"

**操作**：
1. 识别为“修正/反馈”意图 → 先读取 `./workflows/validate.md`
2. 执行 `git pull origin main`
3. 收集错误信息和环境信息
4. 查阅 Unity 官方文档确认 yield return 的正确用法
5. 验证用户报告的具体错误
6. 执行修正流程：
   - 更新解决方案内容为正确写法
   - 添加版本说明和注意事项
   - 状态保持 ✅ 已验证
7. 若标签/状态变化则更新 `./INDEX.md`
8. 执行 `git add . && git commit -m "fix: correct coroutine yield return usage" && git push origin main`
9. 反馈用户修正结果

---

## 使用提示

- 示例可以增长，但建议只保留具有代表性的核心案例
- 长篇内容应移至独立文档（统一写入 `data/` 目录）
- 定期清理过期或过时的示例

## 链接回操作指南

- 详细操作流程：参见 [workflows/record.md](./workflows/record.md)
- 验证流程：参见 [workflows/validate.md](./workflows/validate.md)
