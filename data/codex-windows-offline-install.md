# Codex Windows 桌面版离线安装（绕过 Microsoft Store UI）

**标签**：#windows #tools #ai #experience #troubleshooting
**来源**：实践总结 + OpenAI 官方分发页面 + Microsoft Store 分发链路实测
**收录日期**：2026-04-23
**来源日期**：2026-04-23
**更新日期**：2026-04-23
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方分发链路 + 本机实测）
**适用版本**：Windows 10/11 + Codex 26.421.620.0 + Windows PowerShell Appx 模块

### 概要

OpenAI 的 Codex Windows 桌面版公开入口虽然挂在 Microsoft 分发链路下，但可以在不打开 Microsoft Store 图形界面的前提下完成安装。对本机已验证的稳定路径是：解析 Product ID `9PLM9XGG6VKS` 获取官方 `.msix` 主包，再用 `powershell.exe` 的 `Add-AppxPackage` 本地安装。

### 内容

#### 适用场景

- 需要安装 OpenAI 官方 Codex Windows 桌面版。
- 不希望通过 Microsoft Store 图形界面安装。
- `winget install --source msstore` 因网络或商店链路问题失败，例如 `0x80072efe`。

#### 核心结论

- ✅ Codex 官方 Windows 桌面版的 Microsoft Store Product ID 是 `9PLM9XGG6VKS`。
- ✅ OpenAI 官方页面会给出 Windows 下载入口，但落地分发仍是 Microsoft Store 体系。
- ✅ `winget show --id 9PLM9XGG6VKS --source msstore` 显示该包 `支持脱机分发: true`。
- ✅ 本机最终成功安装的主包是 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix`。
- ✅ 安装成功后，开始菜单入口为 `Codex`，AppUserModelID 为 `OpenAI.Codex_2p2nqsd0c76g0!App`。
- ⚠️ OpenAI 页面返回的 `Codex Installer.exe` 是 Microsoft 的 StoreInstaller 外壳；本机尝试静默参数 `/S` 返回退出码 `1612`，不适合作为当前环境下最稳的无人值守路径。
- ⚠️ 在本机 `pwsh` 环境中，`Add-AppxPackage` 所在的 `Appx` 模块无法正常加载；应改用系统自带的 `powershell.exe` 执行安装与查询。

#### 实测流程

1. 先确认官方分发信息。
   - OpenAI 官方文章《Codex：全能型助手》给出 Windows 下载入口。
   - `winget show --id 9PLM9XGG6VKS --source msstore` 可确认发布者为 OpenAI，安装器类型为 `msstore`，且支持脱机分发。

2. 先尝试命令行直装。
   - `winget install --id 9PLM9XGG6VKS --source msstore --accept-source-agreements --accept-package-agreements --disable-interactivity`
   - 本机该路径失败，错误码为 `0x80072efe`。

3. 回退到离线包安装。
   - 使用 Microsoft Store Product ID `9PLM9XGG6VKS` 在 `store.rg-adguard.net` 上选择 `Retail` 渠道，解析出可下载的主包链接。
   - 获取到主包：`OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix`
   - 获取到 SHA-1：`e6b4f9a813fc55f58131154edf8eb5345f0b2318`

4. 下载并校验主包。
   - 下载后使用 `Get-FileHash -Algorithm SHA1` 校验，结果与分发页一致。

5. 用 Windows PowerShell 安装。
   - 使用 `powershell.exe -NoProfile -Command "Add-AppxPackage -Path <msix路径>"`
   - 本机安装成功，返回无错误。

6. 安装后验证。
   - `Get-AppxPackage` 返回包名 `OpenAI.Codex`，`Status = Ok`
   - `Get-StartApps` 可见 `Codex`
   - `Start-Process 'shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App'` 可拉起应用进程

#### 注意事项

- `store.rg-adguard.net` 解析出来的下载链接带过期时间，失效后需要重新解析，不能长期复用旧直链。
- 该方案准确表述应为“绕过 Microsoft Store UI 安装”，不是“完全脱离 Microsoft Store 后端分发”。
- 如果未来 OpenAI 直接提供独立安装器并且不再套 Microsoft StoreInstaller，优先使用官方直链安装器；当前这台机器上更稳的路径仍然是 `.msix + Add-AppxPackage`。
- 若安装时报缺依赖，应按 `Add-AppxPackage` 的错误提示补装对应依赖包；本次 Codex 主包在当前系统上无需额外依赖包即可完成安装。

### 关键代码

```powershell
# 1) 查看官方包元数据
winget show --id 9PLM9XGG6VKS --source msstore --accept-source-agreements

# 2) 命令行直装（本机失败，错误码 0x80072efe）
winget install --id 9PLM9XGG6VKS --source msstore --accept-source-agreements --accept-package-agreements --disable-interactivity

# 3) 下载离线 msix（链接需重新解析获取最新值）
$dest = Join-Path $env:TEMP 'OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix'
Invoke-WebRequest -Uri '<resolved-msix-url>' -OutFile $dest
Get-FileHash -Algorithm SHA1 $dest

# 4) 用 Windows PowerShell 安装（不要用 pwsh）
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '$dest'"

# 5) 安装后验证
powershell.exe -NoProfile -Command "Get-AppxPackage | Where-Object { $_.Name -like 'OpenAI.Codex*' }"
powershell.exe -NoProfile -Command "Get-StartApps | Where-Object { $_.Name -like '*Codex*' }"
powershell.exe -NoProfile -Command "Start-Process 'shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App'"
```

### 参考链接

- [Codex：全能型助手](https://openai.com/zh-Hans-CN/index/codex-for-almost-everything/) - OpenAI 官方产品发布页，包含 Windows 下载入口
- [Codex - Free download and install on Windows](https://apps.microsoft.com/detail/9plm9xgg6vks?hl=en-US&gl=US) - Microsoft 应用详情页，对应 Product ID `9PLM9XGG6VKS`
- [Microsoft Store - Generation Project](https://store.rg-adguard.net/) - Microsoft Store CDN 解析工具，用于获取离线分发链接
- [Windows 10上不使用MicroSoft Store下载安装MicroSoft Todo](https://blog.csdn.net/qq_41340996/article/details/119318119) - 通用的 Store 应用离线安装思路参考
- [绕过Microsoft Store安装Microsoft Store应用](https://blog.csdn.net/xiaoye1360715890/article/details/159116253) - 以 Codex 为例的 Product ID 解析思路参考

### 相关记录

- [Windows 下通过 winget 安装 Microsoft Store 应用而不打开商店界面](./windows-winget-msstore-app-install.md) - 当 `msstore` 链路正常时，优先走 `winget`

### 验证记录

- [2026-04-23] 初次记录，来源：本机实测 OpenAI Codex Windows 桌面版安装。
- [2026-04-23] 已验证 `winget show --id 9PLM9XGG6VKS --source msstore` 可确认官方包元数据，且显示“支持脱机分发: true”。
- [2026-04-23] 已验证本机 `winget install --source msstore` 返回 `0x80072efe`，需回退到离线 msix 安装路径。
- [2026-04-23] 已验证 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0.msix` 的 SHA-1 为 `e6b4f9a813fc55f58131154edf8eb5345f0b2318`。
- [2026-04-23] 已验证使用 `powershell.exe` 执行 `Add-AppxPackage` 可完成安装，`Get-AppxPackage` 返回 `OpenAI.Codex_26.421.620.0_x64__2p2nqsd0c76g0`，`Status = Ok`。
- [2026-04-23] 已验证开始菜单入口名称为 `Codex`，且 `shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App` 可成功启动应用。

---