# Microsoft Store AppContainer 代理异常导致 Codex 桌面端启动即退出的修复记录

**标签**：#windows #network #proxy #troubleshooting #experience
**来源**：实践总结（已脱敏）
**收录日期**：2026-04-28
**来源日期**：2026-04-28
**更新日期**：2026-04-28
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本机实测 + 用户确认）
**适用版本**：Windows 10 Enterprise 22H2 19045 x64 + Microsoft Store 22603.1401.15.0 + Microsoft.StorePurchaseApp 22601.1401.7.0 + OpenAI Codex 26.422.8496.0

### 概要

Codex 桌面端启动即退出时，不一定是 Codex 主程序本身损坏；在本案例中，根因是 Codex 启动阶段触发 Store 更新检测，而 Microsoft Store 当前用户注册和网络链路异常。重新注册/更新 Store 组件，并为 Store AppContainer 添加本机代理 loopback 豁免后，Codex 与 Microsoft Store 均恢复可用。

### 内容

#### 问题场景

- Codex 桌面端启动后很快退出。
- Microsoft Store 无法正常打开或无法正常访问后端服务。
- 当前用户使用本机 HTTP/HTTPS 代理，代理监听在 `127.0.0.1:7890`。
- `WinHTTP` 代理为直连，当前用户代理配置为 `127.0.0.1:7890`。
- Store AppContainer loopback 豁免为空，导致 Store 这类 AppContainer 应用不能直接访问本机代理。

#### 关键现象

- Codex 已安装旧版本，启动日志提示 Store 中存在新版本。
- Codex 崩溃点位于 Windows 更新相关 native 模块，异常为访问冲突 `0xC0000005`。
- Store 事件日志中出现 `0x80072EFD` / `0x80072EFE`，请求目标包含 `storeedge.microsoft.com` 或旧版 Store endpoint。
- 当前用户一开始缺少有效的 `Microsoft.WindowsStore` / `Microsoft.StorePurchaseApp` 注册，或版本明显偏旧。
- 重新注册和更新 Store 后，仍需处理 AppContainer 访问本机代理的问题。

#### 原因判断

本案例是多个条件叠加造成的：

1. Codex 启动阶段会检查 Microsoft Store 分发包更新。
2. 本机 Codex 已安装版本低于 Store manifest 中的版本。
3. Store 当前用户注册缺失或版本过旧，导致常规 Store 更新链路不可用。
4. 当前网络依赖本机代理，但 Store AppContainer 没有 loopback 豁免，无法访问 `127.0.0.1:7890`。
5. Store 更新链路失败后，Codex 的 Windows updater native 模块触发崩溃，表现为桌面端启动即退出。

#### 修复步骤

1. 先确认包状态和 Store 日志，不直接假设是 Codex 主程序损坏：

```powershell
powershell.exe -NoProfile -Command "Get-AppxPackage | Where-Object { $_.Name -match 'Microsoft.WindowsStore|Microsoft.StorePurchaseApp|OpenAI.Codex' } | Select-Object Name,PackageFamilyName,Version,Status"
Get-WinEvent -LogName 'Microsoft-Windows-Store/Operational' -MaxEvents 100
```

2. 若当前用户缺少 Store 注册，但系统 `WindowsApps` 中仍存在 Store 包，可重新注册：

```powershell
powershell.exe -NoProfile -Command "Add-AppxPackage -DisableDevelopmentMode -Register '<Microsoft.WindowsStore>\AppxManifest.xml'"
powershell.exe -NoProfile -Command "Add-AppxPackage -DisableDevelopmentMode -Register '<Microsoft.StorePurchaseApp>\AppxManifest.xml'"
```

3. 若 Store 版本过旧，使用官方 Microsoft CDN 解析到的 `.msixbundle` / `.appxbundle` 更新 Store 和 StorePurchaseApp。安装前必须做签名与包校验：

```powershell
Get-AuthenticodeSignature '<package.msixbundle>'
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '<Microsoft.StorePurchaseApp.appxbundle>' -ForceApplicationShutdown"
powershell.exe -NoProfile -Command "Add-AppxPackage -Path '<Microsoft.WindowsStore.msixbundle>' -ForceApplicationShutdown"
```

4. 确认当前用户代理和本机监听端口：

```powershell
Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' |
  Select-Object ProxyEnable, ProxyServer, AutoConfigURL

Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 7890 -State Listen
```

5. 查询 Store AppContainer SID。若 `CheckNetIsolation LoopbackExempt -a -n=<PackageFamilyName>` 在当前环境只返回帮助或失败，可改用 SID：

```powershell
reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings" /s /f "windowsstore"
reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings" /s /f "storepurchase"
```

6. 以管理员权限为 Store 和 StorePurchaseApp 添加 loopback 豁免：

```powershell
CheckNetIsolation LoopbackExempt -a -p=<Microsoft.WindowsStore AppContainer SID>
CheckNetIsolation LoopbackExempt -a -p=<Microsoft.StorePurchaseApp AppContainer SID>
CheckNetIsolation LoopbackExempt -s
```

7. 重启 Microsoft Store 并检查新日志：

```powershell
Get-Process WinStore.App -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Process explorer.exe 'shell:AppsFolder\Microsoft.WindowsStore_8wekyb3d8bbwe!App'
```

#### 验证标准

- `Get-AppxPackage` 显示以下包均为 `Status = Ok`：
  - `OpenAI.Codex`
  - `Microsoft.WindowsStore`
  - `Microsoft.StorePurchaseApp`
- `CheckNetIsolation LoopbackExempt -s` 能看到：
  - `microsoft.windowsstore_8wekyb3d8bbwe`
  - `microsoft.storepurchaseapp_8wekyb3d8bbwe`
- Store 重启后事件日志中不再出现 `0x80072EFD` / `0x80072EFE`。
- Store 后端请求出现成功响应，例如 `displaycatalog.mp.microsoft.com` 返回 `protocolStatusCode = 200`。
- Codex 桌面端启动后保持运行，不再立即退出。
- 用户实际确认 Microsoft Store 可以打开。

#### 时效性与边界

- 本记录的版本环境截至 `2026-04-28` 已验证；Microsoft Store、StorePurchaseApp、Codex 的版本号会随官方发布变化，不能把记录中的版本当作长期最新版本。
- Store CDN 解析出的下载直链通常带过期时间，不能长期复用；每次处理都应重新解析并校验签名。
- 如果 Store 日志已经没有 `0x80072EFD` / `0x80072EFE`，不要继续修改 `WinHTTP` 全局代理，避免扩大影响面。
- Store 在代理环境下可能仍出现 `Certificate is not valid for Microsoft root` 警告；如果页面可打开且服务请求成功，该警告不一定是阻塞原因。若页面仍空白，应优先检查代理是否对 Microsoft Store 相关域名做了 HTTPS 解密或错误分流。

#### 脱敏说明

本记录已脱敏：

- 不记录本机用户名、项目路径、崩溃转储路径、设备 ID、设备型号。
- 不记录具体代理客户端名称，只记录必要的代理形态：本机代理监听在 `127.0.0.1:7890`。
- 不记录一次性下载 URL，只保留“官方 Microsoft CDN 包 + 签名校验 + Appx 安装”的流程。

### 关键代码

```powershell
# 包状态检查
powershell.exe -NoProfile -Command "Get-AppxPackage | Where-Object { $_.Name -match 'Microsoft.WindowsStore|Microsoft.StorePurchaseApp|OpenAI.Codex' } | Select-Object Name,PackageFamilyName,Version,Status"

# 当前用户代理检查
Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' |
  Select-Object ProxyEnable, ProxyServer, AutoConfigURL

# 本机代理监听检查
Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 7890 -State Listen

# Store AppContainer 映射查询
reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings" /s /f "windowsstore"
reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings" /s /f "storepurchase"

# 管理员权限执行：添加 loopback 豁免
CheckNetIsolation LoopbackExempt -a -p=<Microsoft.WindowsStore AppContainer SID>
CheckNetIsolation LoopbackExempt -a -p=<Microsoft.StorePurchaseApp AppContainer SID>
CheckNetIsolation LoopbackExempt -s
```

### 参考链接

- [Add-AppxPackage](https://learn.microsoft.com/powershell/module/appx/add-appxpackage) - Appx/MSIX 本地安装官方命令说明
- [CheckNetIsolation](https://learn.microsoft.com/windows/win32/api/) - Windows AppContainer 网络隔离相关系统工具入口
- [Microsoft Store - Generation Project](https://store.rg-adguard.net/) - Microsoft Store CDN 包解析工具

### 相关记录

- [Windows 下不打开 Microsoft Store UI 安装 Store 应用的通用路径](./windows-winget-msstore-app-install.md) - Store 应用绕过 UI 安装和离线包安装的通用路径
- [Git for Windows 不继承系统代理时的处理方式](./git-windows-system-proxy-not-inherited.md) - Windows 命令行工具与系统代理不一致时的相关排障经验

### 验证记录

- [2026-04-28] 已验证 Codex 从旧版本更新到 `26.422.8496.0` 后，桌面端启动保持运行，不再立即退出。
- [2026-04-28] 已验证 `Microsoft.WindowsStore` 更新到 `22603.1401.15.0`，`Microsoft.StorePurchaseApp` 更新到 `22601.1401.7.0`，二者 `Status = Ok`。
- [2026-04-28] 已验证 Store 和 StorePurchaseApp 的 AppContainer loopback 豁免写入成功。
- [2026-04-28] 已验证 Store 重启后 `0x80072EFD` / `0x80072EFE` 出现次数为 0，失败服务请求数为 0，并出现 Microsoft Store 服务请求 `200` 响应。
- [2026-04-28] 用户确认 Microsoft Store 已能打开。

---
