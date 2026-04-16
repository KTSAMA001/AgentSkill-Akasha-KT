# Windows 下通过 winget 安装 Microsoft Store 应用而不打开商店界面

**标签**：#windows #tools #experience #troubleshooting
**来源**：实践总结 + Microsoft 官方分发链路实测
**收录日期**：2026-04-16
**来源日期**：2026-04-16
**更新日期**：2026-04-16
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (本机实测 + 官方分发链路)
**适用版本**：Windows 10/11 + winget 1.12.x + msstore source

### 概要

当目标应用只有 Microsoft Store 分发渠道时，仍可通过 `winget` 直接从 `msstore` 源安装，而不需要打开 Microsoft Store 图形界面。本记录验证了这一做法对 `Microsoft To Do` 可行，并总结了更可靠的安装后校验方式。

### 内容

#### 适用场景

- 需要安装仅在 Microsoft Store 上发布的免费应用。
- 用户不希望手动打开 Microsoft Store 界面。
- 当前系统已具备 `winget`，且 `msstore` 源可用。

#### 核心结论

- ✅ 可以使用 `winget` 直接安装 `msstore` 应用，而不打开 Microsoft Store 图形界面。
- ✅ 这种方式仍然走微软官方分发链路，本质上是“绕过 Store UI”，不是“绕过 Microsoft Store 后端”。
- ✅ 对 `Microsoft To Do` 的实测安装命令可成功完成安装。
- ⚠️ 安装完成后，`winget list` 对 `msstore` 应用的回显不一定稳定或及时；更可靠的校验方式是 `Get-AppxPackage` 与 `Get-StartApps`。

#### 实测流程

1. 先确认 `winget` 已安装，并且存在 `msstore` 源。
2. 使用 `winget search` 或 `winget show` 确认应用的 Store Product ID。
3. 通过 `winget install --source msstore` 执行安装。
4. 用系统侧命令确认 AppX 包已注册，并确认开始菜单中可发现应用。

#### 实测案例：Microsoft To Do

- 应用名称：`Microsoft To Do: Lists, Tasks & Reminders`
- Store Product ID：`9NBLGGH5R558`
- `winget show` 可见安装器类型为 `msstore`，并显示“支持脱机分发: true”。
- 实测安装成功后，系统中出现包：`Microsoft.Todos_2.175.6901.0_x64__8wekyb3d8bbwe`
- 开始菜单可发现应用名称：`Microsoft To Do`

#### 注意事项

- 该方案适合免费、可由当前用户直接获取的 Store 应用；若应用有地区、账号或授权限制，仍可能无法安装。
- 若系统中缺少 `winget` 或 `msstore` 源不可用，此方案无法直接执行。
- 不要把这种方式表述成“完全脱离微软商店安装”；准确说法是“不打开微软商店界面安装”。
- 对这类应用，优先记录 Store Product ID，而不是模糊应用名，避免 `winget search` 命中歧义结果。

### 关键代码（如有）

```powershell
# 检查 winget 与源
winget --version
winget source list

# 查询应用
winget show --id 9NBLGGH5R558 --source msstore --accept-source-agreements

# 安装应用（不打开 Microsoft Store UI）
winget install --id 9NBLGGH5R558 --source msstore --accept-source-agreements --accept-package-agreements --disable-interactivity

# 更可靠的安装后校验
Get-AppxPackage -Name Microsoft.Todos | Select-Object Name, PackageFullName, Status
Get-StartApps | Where-Object { $_.Name -like '*To Do*' -or $_.Name -like '*Todo*' } | Select-Object Name, AppID
```

### 参考链接（如有）

- [Use the winget tool to install and manage applications](https://learn.microsoft.com/windows/package-manager/winget/) - Windows Package Manager 官方文档
- [winget install command](https://learn.microsoft.com/windows/package-manager/winget/install) - `winget install` 官方命令说明

### 相关记录（如有）

- [Windows 系统 PATH 缺失关键目录导致工具检测失败（以 Claude Code 为案例）](./windows-system-path-missing-app-detection-failure.md) - Windows 工具链排障的另一类环境问题

### 验证记录

- [2026-04-16] 初次记录，来源：本机实测 `Microsoft To Do` 安装流程。
- [2026-04-16] 已验证 `winget install --id 9NBLGGH5R558 --source msstore` 可在不打开 Microsoft Store 图形界面的前提下完成安装。
- [2026-04-16] 已验证 `Get-AppxPackage -Name Microsoft.Todos` 返回 `Status = Ok`，且开始菜单可发现 `Microsoft To Do`。

---