# 使用示例合集

> 经验记录系统使用示例集合

---

## 一、查找已有经验

### 示例 1：Unity 协程问题

**用户**："Unity 协程怎么正确等待一帧？"

**操作**：
1. 判断为 Unity C# 相关 → 读取 `../data/unity-framework-architecture.md`
2. 搜索关键词"协程"、"yield"、"等待"
3. 找到相关记录 → 展示给用户
4. 反馈："在经验记录中找到相关内容，建议使用 `yield return null` 替代 `yield return 0`"

---

### 示例 2：网络搜索

**用户**："Unity DOTS 的 IJobEntity 怎么用？"

**操作**：
1. 判断为 Unity 相关 → 读取 `../data/unity-framework-architecture.md`
2. 搜索关键词"DOTS"、"IJobEntity"、"Job"
3. 未找到相关记录 → 告知用户："未在经验记录中找到相关内容，正在上网搜索..."
4. 搜索 Unity 官方文档关于 DOTS/IJobEntity 的内容
5. 整理搜索结果并展示解决方案
6. 询问："问题解决了吗？需要将此经验记录下来吗？"

---

## 二、记录新经验

### 示例 3：记录 Unity 协程优化

**用户**："帮我记录一下刚才解决的 Unity 协程问题"

**操作**：
1. 执行 `git pull origin main` 拉取仓库最新内容
2. 识别为 Unity C# 协程相关 → 归类到 `unity-framework-architecture.md`
3. 检查是否有类似记录 → 无
4. 提取关键信息：
   - 标题：Unity 协程优化
   - 问题：协程中使用 yield return 0 导致性能问题
   - 解决：使用 yield return null 更高效
5. 追加到 `unity-framework-architecture.md`
6. 执行 `git add . && git commit -m "update: 添加 Unity 协程优化经验" && git push origin main`
7. 反馈："已将协程优化经验记录到 unity-framework-architecture.md，并已同步到远程仓库"

---

## 三、更新已有经验

### 示例 4：补充协程注意事项

**用户**："刚才那个协程问题，我发现还有个注意点要补充"

**操作**：
1. 执行 `git pull origin main` 拉取仓库最新内容
2. 定位到 `unity-framework-architecture.md` 中的协程相关记录
3. 判断为"补充"类型更新
4. 添加更新日期、新增内容
5. 提交并推送

---

## 四、大型架构文档

### 示例 5：保存 VR 变体收集器架构

**用户**："把这个 VR 变体收集器的完整设计文档保存下来"

**操作**：
1. 执行 `git pull origin main`
2. 识别为大型内容，符合 Progressive Disclosure 原则
3. 创建独立文档：`../data/vr-variant-collector-architecture.md`
4. 编写完整架构设计、打包策略、编译坑点
5. 在 `unity-shader-variants-tool.md` 中追加记录：
   - 标题：VR Shader 变体收集器架构
   - 内容：摘要核心的打包策略和优化点
   - 链接：`- [完整架构文档](./vr-variant-collector-architecture.md)`
6. 提交并推送

---

## 五、错误经验处理

### 示例 6：WWW 类废弃

**用户**："这个 WWW 类的用法是不是过时了？"

**操作**：
1. 搜索 Unity 官方文档确认 WWW 已在 Unity 2018.3 后被标记为 Obsolete
2. 执行废弃流程：
   - 在原记录标题后添加 `[已废弃]` 标记
   - 状态改为 🔄 已过时
   - 在开头添加废弃警告
   - 添加替代方案：推荐使用 UnityWebRequest
3. 添加验证记录

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
1. 分析冲突原因：这是适用场景不同，不是正确性问题
2. 在两条经验中添加"相关经验"链接，互相引用
3. 明确标注各自的适用条件：
   - **async/await**：适用于纯计算、文件 IO、网络请求等不依赖 Unity 主线程
   - **协程**：适用于等待帧、物理更新、UnityWebRequest 等 Unity 特有异步
4. 添加备注说明选择依据

---

## 七、用户反馈处理

### 示例 8：经验验证失败

**用户**："你之前记录的那个 Unity 协程用 yield return 0 的说法好像不对，我试了报错"

**操作**：
1. 收集错误信息和环境信息
2. 查阅 Unity 官方文档确认 yield return 的正确用法
3. 验证用户报告的具体错误
4. 执行修正流程：
   - 更新解决方案内容为正确写法
   - 添加版本说明和注意事项
   - 状态保持 ✅ 已验证
5. 反馈用户修正结果

---

## 使用提示

- 示例可以增长，但建议只保留具有代表性的核心案例
- 长篇内容应移至独立文档（如 docs/ 目录）
- 定期清理过期或过时的示例

## 链接回操作指南

- 详细操作流程：参见 [workflows/record.md](./workflows/record.md)
- 验证流程：参见 [workflows/validate.md](./workflows/validate.md)
