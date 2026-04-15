# Windows 系统 PATH 缺失关键目录导致工具检测失败（以 Claude Code 为案例）

**标签**：#vscode #tools #experience #claude-code #git #bug
**来源**：实践总结（Windows 本地环境排障）
**收录日期**：2026-03-02
**来源日期**：2026-03-02
**更新日期**：2026-03-02
**状态**：✅ 已验证
**可信度**：⭐⭐⭐
**适用版本**：Windows 10/11 + VS Code 扩展生态（依赖系统命令探测场景）

### 概要
当应用或扩展通过进程调用系统命令（如 `where.exe`）探测依赖时，若系统 `PATH` 缺失 `C:\Windows\System32` 等关键目录，会出现“明明已安装依赖却被判定缺失”的假故障。本记录沉淀一套可复用的定位与修复流程。

### 内容

#### 典型现象

- 工具提示缺少依赖（如 git/bash），但手动检查发现依赖实际已安装。
- 在终端中部分命令可用，但在应用内的探测逻辑中失败。
- 反复设置应用级环境变量无效，重装依赖也无效。

#### 根因模式（通用）

- 依赖探测通常走“子进程调用系统命令”路径（例如 `spawnSync("where.exe", ["git"])`）。
- 该路径依赖当前进程的环境变量，尤其是 `PATH`。
- 当系统级 `PATH` 缺失 `System32` 相关目录时，`where.exe` 本身不可达，导致后续依赖判断链路整体失真。

#### 诊断流程（推荐顺序）

1. **先验证依赖本体是否真实存在**
   - 如 `git.exe`、`bash.exe` 的实际安装路径。
2. **再验证“探测命令”本身是否可达**
   - 重点确认 `where.exe` 是否能被当前进程找到。
3. **检查系统级 PATH 是否完整**
   - 重点核对：
     - `C:\Windows\System32`
     - `C:\Windows`
     - `C:\Windows\System32\Wbem`
     - `C:\Windows\System32\WindowsPowerShell\v1.0`
4. **区分“用户级变量”与“系统级变量”**
   - 某些应用探测在进程继承链上更依赖系统级 PATH。
5. **修复后进行“完整进程重启”验证**
   - 仅 Reload Window 可能不足；需确保宿主应用及相关后台进程完全重启。

#### 修复策略（通用）

- 优先修复系统 PATH 的完整性，再做应用级兜底变量配置。
- 避免只在单个工具配置中硬编码路径而忽略系统环境异常。
- 修复后使用“应用真实探测路径”回归，而不仅是手工命令回归。

#### 案例映射（本次）

- 场景：VS Code 中 Claude Code 扩展提示需要 git-bash。
- 现象：`git` 与 Git Bash 均已安装，但扩展仍报错。
- 根因：系统 `PATH` 缺失 `C:\Windows\System32`，导致扩展内部探测链路调用 `where.exe` 失败。
- 结果：补齐系统 PATH 关键目录并完整重启 VS Code 后恢复正常。

### 关键代码（如有）

```powershell
# 查看系统级 PATH
[Environment]::GetEnvironmentVariable('Path', 'Machine')

# 查看用户级 PATH
[Environment]::GetEnvironmentVariable('Path', 'User')
```

### 参考链接（如有）

- [Windows where 命令文档](https://learn.microsoft.com/windows-server/administration/windows-commands/where) - 依赖探测常见基础命令
- [Node.js child_process.spawnSync](https://nodejs.org/api/child_process.html#child_processspawnsynccommand-args-options) - 扩展/工具常用的子进程调用机制

### 相关记录（如有）

- [claude-code-comprehensive-guide](./claude-code-comprehensive-guide.md) - Claude Code 功能与使用总览

### 验证记录
- [2026-03-02] 初次记录，来源：本地 Windows 环境实战排障。
- [2026-03-02] 已在目标环境验证：补齐系统 PATH 后，应用内依赖探测恢复正常。

---
