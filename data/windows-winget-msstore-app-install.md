# Windows 下不打开 Microsoft Store UI 安装 Store 应用的通用路径

**标签**：#windows #tools #experience #troubleshooting
**来源**：实践总结 + Microsoft / OpenAI 官方分发链路实测
**收录日期**：2026-04-16
**来源日期**：2026-04-16
**更新日期**：2026-04-23
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本机实测 + 官方分发链路）
**适用版本**：Windows 10/11 + winget 1.12.x + msstore source + Windows PowerShell Appx 模块

### 概要

当目标应用只通过 Microsoft Store 分发时，不一定要打开 Microsoft Store 图形界面。已验证的通用做法有两条：优先走 `winget + msstore` 直装；若商店链路失败但包支持脱机分发，则回退到 `.msix/.appxbundle + Add-AppxPackage` 的离线安装路径。`Microsoft To Do` 和 `Codex` 只是这套方法的两个案例。

### 内容

#### 适用场景

- 目标应用只有 Microsoft Store 分发渠道。
- 不希望打开 Microsoft Store 图形界面。
- 需要在网络受限、商店异常、企业环境或无人值守场景下安装应用。

#### 核心结论

- ✅ “不打开 Microsoft Store UI 安装”与“完全脱离 Microsoft Store 后端分发”不是一回事。前者可行，后者通常不准确。
- ✅ 首选路径应是 `winget install --source msstore`，因为最省步骤，且仍走官方分发链路。
- ✅ 若 `winget install` 因网络、商店链路或当前环境问题失败，可回退到离线包安装：先解析 Product ID 获取 `.msix/.appxbundle` 主包，再用 `Add-AppxPackage` 本地安装。
- ✅ 判断某包是否适合走离线路径，最直接的检查是 `winget show` 中是否出现“支持脱机分发: true”。
- ✅ 安装完成后的可靠校验方式应优先使用 `Get-AppxPackage` 和 `Get-StartApps`，不要只看 `winget list`。
- ⚠️ `winget download` 对部分 `msstore` 包可能要求 Microsoft Entra ID 身份验证，不能把它当成稳定的通用离线下载方案。
- ⚠️ 在某些机器上 `pwsh` 虽然能解析到 `Add-AppxPackage`，但无法正常加载 `Appx` 模块；此时应改用系统自带的 `powershell.exe`。

#### 路径选择

| 路径 | 适用条件 | 优点 | 风险/限制 |
|------|----------|------|-----------|
| 路径 A：`winget + msstore` | `msstore` 链路正常，当前用户可直接获取应用 | 步骤最少，命令最标准 | 受商店网络链路、账号、地区限制影响 |
| 路径 B：`.msix/.appxbundle + Add-AppxPackage` | 包支持脱机分发，且能解析到安装包直链 | 可绕过 Store UI 和部分商店异常 | 需自己处理依赖包、链接过期、PowerShell/Appx 环境问题 |

#### 通用流程

##### 1. 先确认 Product ID 和包元数据

- 用应用商店详情页或 `winget search/show` 确认 Product ID。
- 推荐先执行：

```powershell
winget show --id <product-id> --source msstore --accept-source-agreements
```

- 重点看三项：
  - 发布者是否可信
  - 安装器类型是否为 `msstore`
  - 是否显示“支持脱机分发: true”

##### 2. 先走路径 A：`winget + msstore`

```powershell
winget install --id <product-id> --source msstore --accept-source-agreements --accept-package-agreements --disable-interactivity
```

- 成功则直接进入安装后验证。
- 失败时不要立刻放弃，先记录错误码，再判断是否切换到路径 B。

##### 3. 失败后切换到路径 B：离线包安装

1. 用 Product ID 在官方分发入口或 `store.rg-adguard.net` 解析出 `.msix` / `.appxbundle` 主包链接。
2. 下载主包，并按需要下载依赖包。
3. 若是 `.msix` 且系统依赖已齐全，通常可直接安装。
4. 若是 `.appxbundle` 或安装时报缺依赖，应同时安装或通过 `-DependencyPath` 补齐依赖包，如 `Microsoft.UI.Xaml`、`Microsoft.VCLibs`、`Microsoft.NET.Native.*`。
5. 使用 Windows PowerShell 安装：

```powershell
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '<package-path>'"
```

带依赖安装示例：

```powershell
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '<bundle-path>' -DependencyPath '<dep1>','<dep2>'"
```

##### 4. 安装后验证

```powershell
powershell.exe -NoProfile -Command "Get-AppxPackage | Where-Object { $_.Name -like '*<keyword>*' }"
powershell.exe -NoProfile -Command "Get-StartApps | Where-Object { $_.Name -like '*<keyword>*' }"
```

- 只要 `Get-AppxPackage` 返回 `Status = Ok`，并且 `Get-StartApps` 能发现应用入口，基本可以判定安装成功。

#### 实测案例

##### 案例 A：Microsoft To Do 走路径 A 成功

- 应用：`Microsoft To Do: Lists, Tasks & Reminders`
- Product ID：`9NBLGGH5R558`
- `winget show` 显示安装器类型 `msstore`，且“支持脱机分发: true”。
- 直接执行 `winget install --id 9NBLGGH5R558 --source msstore ...` 安装成功。
- `Get-AppxPackage -Name Microsoft.Todos` 返回 `Status = Ok`。
- 开始菜单可发现 `Microsoft To Do`。

##### 案例 B：Codex 走路径 A 失败，路径 B 成功

- 应用：`Codex`
- Product ID：`9PLM9XGG6VKS`
- `winget show` 同样显示“支持脱机分发: true”。
- 本机执行 `winget install --id 9PLM9XGG6VKS --source msstore ...` 返回 `0x80072efe`。
- 回退到离线包路径后，解析得到主包 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix`。
- 校验 SHA-1：`e6b4f9a813fc55f58131154edf8eb5345f0b2318`
- 使用 `powershell.exe` 执行 `Add-AppxPackage` 安装成功。
- `Get-AppxPackage` 返回 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0`，`Status = Ok`。
- `Get-StartApps` 可见 `Codex`。

#### 常见坑

- `store.rg-adguard.net` 解析出的下载直链通常带过期时间，不能长期缓存使用。
- Product ID 比应用名更稳定，优先记录 Product ID，避免搜索命中歧义。
- 某些应用页面给出的 `get.microsoft.com/installer/download/<product-id>` 只是 Microsoft 的 StoreInstaller 包装层，不等于真正可稳定静默部署的独立安装器。
- 如果 `Add-AppxPackage` 报缺依赖，不要强行重试主包；应先按错误信息补齐依赖包再安装。
- 浏览器或 `Invoke-WebRequest` 能访问 GitHub/Microsoft，不代表 `git` 或 `winget` 一定能复用同一代理链路；命令行工具常需要单独处理代理配置。

### 关键代码

```powershell
# 1) 检查 winget 与 msstore 源
winget --version
winget source list

# 2) 查询应用元数据
winget show --id <product-id> --source msstore --accept-source-agreements

# 3) 路径 A：直接安装
winget install --id <product-id> --source msstore --accept-source-agreements --accept-package-agreements --disable-interactivity

# 4) 路径 B：下载离线主包（实际 URL 需实时解析）
$package = Join-Path $env:TEMP '<package-name>.msix'
Invoke-WebRequest -Uri '<resolved-package-url>' -OutFile $package
Get-FileHash -Algorithm SHA1 $package

# 5) 用 Windows PowerShell 安装
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '$package'"

# 6) 若缺依赖，带依赖安装
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '<bundle-path>' -DependencyPath '<dep1>','<dep2>'"

# 7) 安装后验证
powershell.exe -NoProfile -Command "Get-AppxPackage | Select-Object Name,PackageFullName,Status"
powershell.exe -NoProfile -Command "Get-StartApps | Select-Object Name,AppID"
```

### 参考链接

- [Use the winget tool to install and manage applications](https://learn.microsoft.com/windows/package-manager/winget/) - Windows Package Manager 官方文档
- [winget install command](https://learn.microsoft.com/windows/package-manager/winget/install) - `winget install` 官方命令说明
- [Add-AppxPackage](https://learn.microsoft.com/powershell/module/appx/add-appxpackage) - Appx/MSIX 本地安装官方命令说明
- [Microsoft Store - Generation Project](https://store.rg-adguard.net/) - Microsoft Store CDN 解析工具
- [Windows 10上不使用MicroSoft Store下载安装MicroSoft Todo](https://blog.csdn.net/qq_41340996/article/details/119318119) - 以 To Do 为例的离线安装思路
- [绕过Microsoft Store安装Microsoft Store应用](https://blog.csdn.net/xiaoye1360715890/article/details/159116253) - 以 Codex 为例的 Product ID 解析思路

### 相关记录

- [git-windows-system-proxy-not-inherited.md](./git-windows-system-proxy-not-inherited.md) - 当 `git`/命令行工具不继承系统代理时的排障路径
- [windows-system-path-missing-app-detection-failure.md](./windows-system-path-missing-app-detection-failure.md) - Windows 工具链环境异常的另一类常见问题

### 验证记录

- [2026-04-16] 初次验证路径 A，案例：`Microsoft To Do`，`winget install --id 9NBLGGH5R558 --source msstore` 成功。
- [2026-04-16] 已验证 `Get-AppxPackage -Name Microsoft.Todos` 返回 `Status = Ok`，且开始菜单可发现 `Microsoft To Do`。
- [2026-04-23] 补充验证路径 B，案例：`Codex`，`winget install --id 9PLM9XGG6VKS --source msstore` 返回 `0x80072efe`，需回退到离线安装。
- [2026-04-23] 已验证 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix` 的 SHA-1 为 `e6b4f9a813fc55f58131154edf8eb5345f0b2318`。
- [2026-04-23] 已验证使用 `powershell.exe` 执行 `Add-AppxPackage` 可完成 Codex 安装，`Get-AppxPackage` 返回 `Status = Ok`，且开始菜单可发现 `Codex`。

---