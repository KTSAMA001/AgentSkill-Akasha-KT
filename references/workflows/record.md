# 记录流程

> 将有价值的内容保存到对应分类文件

---

## 一、流程总览

1. **同步仓库**：`git pull origin main`
2. **判断类型** → 经验 vs 知识
3. **确定分类** → 参考 [INDEX.md](../INDEX.md)
4. **全面验证** → 按 [validate.md](./validate.md) 流程进行验证检查（包括重复检测、正确性、时效性等）
5. **格式化与写入** → [experience template](../templates/experience-template.md) / [knowledge template](../templates/knowledge-template.md)
6. **提交与反馈** → Git Commit & User Feedback

---

## 二、记录经验 (Experience)

> **核心问题**：怎么解决？怎么做？
> **侧重**：问题 → 方案 → 验证

### 2.1 推荐分类
参考 [INDEX.md](../INDEX.md) 中的**经验分类表**查看所有可用分类及其文件。根据内容性质选择对应分类：
- **Unity 相关** → `experiences/unity/*`
- **编程语言** → `experiences/csharp/`、`experiences/python/` 等
- **工具/开发** → `experiences/tools/`、`experiences/git/` 等
- **其他领域** → `experiences/ai/`、`experiences/shader/` 等

### 2.2 提取要点清单
- **标题**：一句话概括问题与方案
- **问题描述**：发生的场景、报错信息
- **解决方案**：具体的修复步骤或代码
- **代码片段**：关键代码（非整文件）
- **版本环境**：Unity 202x, VS Code xxx
- **参考链接**：StackOverflow, Unity Forum

---

## 三、记录知识 (Knowledge)

> **核心问题**：是什么？为什么？
> **侧重**：定义 → 原理 → 要点

### 3.1 推荐分类
参考 [INDEX.md](../INDEX.md) 中的**知识分类表**查看所有可用分类及其文件。根据知识性质选择对应分类：
- **图形学** → `knowledge/graphics/`、`knowledge/hlsl/`
- **编程** → `knowledge/programming/csharp.md`
- **工具** → `knowledge/tools/*`
- **其他** → `knowledge/ai/`、`knowledge/social/` 等

### 3.2 提取要点清单
- **标题**：知识点名称
- **定义**：简练的概念解释
- **原理**：底层逻辑或工作机制
- **来源**：官方文档、权威书籍
- **示例**：简单的用法演示

---

## 四、高级处理

### 4.1 跨分类处理 (交叉引用)
当内容涉及多个领域时（如 Unity 中的 C# 特性）：
1. **主分类写入**：在最核心的分类文件中记录
   - 判定标准：问题发生层 / 解决方案层
2. **相关分类引用**：
   ```markdown
   > 另见：[标题](../../主分类/文件.md#anchor) —— 一句话说明
   ```

### 4.2 大型内容 (Docs)
> 对 >50 行或完整方案，使用独立文档

1. 创建 `[分类]/docs/[name].md`
2. 主文件添加摘要 + 链接

---

## 五、仓库同步与规范

### Commit 规范
`git commit -m "Type: Subject"`

| 类型 | 格式示例 |
|------|----------|
| **新增经验** | `docs: add experience [标题]` |
| **新增知识** | `docs: add knowledge [标题]` |
| **更新内容** | `docs: update [文件名] - [说明]` |
| **修正错误** | `fix: correct [文件名] - [错误]` |

### 冲突解决
```bash
git pull --rebase origin main
# 解决冲突
git add . && git rebase --continue
git push origin main
```
