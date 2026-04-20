# Git for Windows 不继承系统代理导致 push/clone 卡死

**标签**：#git #windows #network #proxy #troubleshooting #experience
**来源**：实践总结
**收录日期**：2026-04-20
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Git for Windows 2.x（使用内置 libcurl，HTTPS 走 schannel/openssl）

### 概要

浏览器能正常打开 GitHub，但 `git clone` / `git push` / `git ls-remote` 报 `Failed to connect to github.com port 443` 或 `Recv failure: Connection was aborted`。根因：Windows「Internet 选项 → 代理服务器」只对 WinINET 生效（IE/Edge/Chrome/PowerShell `Invoke-WebRequest` 走这条），而 Git for Windows 使用 libcurl，**不会自动读 WinINET 代理**，环境变量 `HTTP(S)_PROXY` 与 `git config http.proxy` 都未设置时就直连，被网络阻断时间窗内必失败。

### 内容

#### 一、典型现象（共存矛盾即可定性）

| 验证项 | 结果 | 说明 |
|--------|------|------|
| 浏览器打开 `https://github.com` | ✅ 200 | WinINET 走系统代理 OK |
| `Invoke-WebRequest -Uri https://github.com` | ✅ 200 | PowerShell 默认走 WinINET |
| `Test-NetConnection github.com -Port 443` | ❌ TcpTestSucceeded=False | 直连 TCP 被阻断 |
| `git ls-remote origin HEAD` | ❌ Failed to connect / Recv failure aborted | libcurl 走直连，被阻断 |

只要满足「浏览器能开 + git 直连失败 + 系统代理已开启但 git 未配代理」，基本可确诊为本问题，无需更多排查。

#### 二、五步定位法

每一步都有判定线索，按顺序执行可在 1 分钟内定位：

1. **看 Git 是否已配代理**
   ```powershell
   git config --show-origin --get-regexp "http\..*proxy|https\..*proxy"
   ```
   - 输出为空 → Git 没配代理
   - 有输出但端口已死 → Git 配了过期代理（清掉再走系统代理那一支）

2. **看进程级环境变量代理**
   ```powershell
   Get-ChildItem Env: | Where-Object { $_.Name -match '^(HTTP|HTTPS|ALL)_PROXY|NO_PROXY$' }
   ```
   - 为空 → 当前 shell 没有代理
   - 有值但端口连不上 → 旧值残留，需清理

3. **看 WinINET 系统代理（关键反差点）**
   ```powershell
   $s = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
   [pscustomobject]@{ ProxyEnable=$s.ProxyEnable; ProxyServer=$s.ProxyServer; AutoConfigURL=$s.AutoConfigURL }
   ```
   - `ProxyEnable=1` 而前两步都为空 → **就是本问题**：浏览器有代理，Git 没继承
   - `ProxyServer` 给出本地代理端口（如 `127.0.0.1:7893`），即可作为 Git 代理

4. **看 WinHTTP 代理（系统服务/部分 SDK 使用）**
   ```powershell
   netsh winhttp show proxy
   ```
   - 与 WinINET 是两套独立配置，多数代理软件只设 WinINET
   - 通常显示「直接访问」，对本问题无直接影响，仅作旁证

5. **测本地代理端口可达性**
   ```powershell
   Test-NetConnection 127.0.0.1 -Port 7893
   curl.exe -I -x http://127.0.0.1:7893 https://github.com --max-time 20
   ```
   - 端口可达且 curl 经代理拿到 200 → 可以把它配给 Git

#### 三、修复方案（按副作用从小到大）

##### 方案 A：单次验证（不写入配置）

```powershell
git -c http.proxy=http://127.0.0.1:7893 -c https.proxy=http://127.0.0.1:7893 push
```

- 适用：临时验证、CI 脚本、不想污染全局配置
- 退出后无残留，是排查阶段最稳的写法

##### 方案 B：仅作用于 GitHub（推荐日常使用）

```powershell
git config --global http.https://github.com.proxy http://127.0.0.1:7893
git config --global https.https://github.com.proxy http://127.0.0.1:7893
```

- 仅访问 `github.com` 时走代理，访问公司内网 / Gitee / 自建 GitLab 时直连，不互相干扰
- 取消：把 `http.https://github.com.proxy` 用 `--unset` 删掉

##### 方案 C：全局代理（仅当所有 Git 远端都需要代理时）

```powershell
git config --global http.proxy http://127.0.0.1:7893
git config --global https.proxy http://127.0.0.1:7893
```

- 缺点：访问内网 Git 也会被强制走代理，常导致内网仓库不可达
- 取消：`git config --global --unset http.proxy ; git config --global --unset https.proxy`

##### 方案 D：环境变量（影响所有 libcurl/HTTP 工具）

```powershell
[Environment]::SetEnvironmentVariable('HTTPS_PROXY','http://127.0.0.1:7893','User')
[Environment]::SetEnvironmentVariable('HTTP_PROXY','http://127.0.0.1:7893','User')
```

- 影响 Git、curl、pip、npm、yarn 等所有走 libcurl/标准 HTTP 的工具
- 配合 `NO_PROXY=localhost,127.0.0.1,.local,.lan,<内网域>` 避免内网误代理
- 优先级：命令行 `-c` > git config > 环境变量

#### 四、易踩的坑

- **代理软件改了端口而忘了同步**：本地代理常见端口（7890/7891/7893/7897/10808/1080）随版本/客户端变化，重启电脑或更新软件后端口可能不同，旧 git config 直接失效。**修复前先用方案 A 测当前可用端口。**
- **socks5 vs http**：`ProxyServer=socks=127.0.0.1:7893` 和 `http=127.0.0.1:7893` 虽然指向同一软件，但 Git 走 HTTPS 时**只能用 http(s) 代理**，不能填 socks5（除非客户端明确支持 socks5h）。读注册表时按 `http=` 那一段配 Git。
- **WinHTTP ≠ WinINET**：`netsh winhttp show proxy` 显示「直接访问」不代表系统没代理，绝大多数桌面代理软件只设 WinINET，看 WinINET 注册表才准。
- **错误现象时好时坏**：代理软件的规则路由（`DIRECT`/`PROXY`）会随节点切换变化，github 短时直连+长期失败的情况，先按本流程定位再判断。

#### 五、根因记忆点

| 通道 | 配置位置 | 谁会用 |
|------|---------|--------|
| WinINET | 注册表 `Internet Settings` / 控制面板 → Internet 选项 | IE / Edge / Chrome / `Invoke-WebRequest` 默认 |
| WinHTTP | `netsh winhttp` | Windows Update / 部分系统服务 / 某些 .NET SDK |
| 环境变量 `HTTP(S)_PROXY` | 进程/用户/系统级 | libcurl / Node / Python / 大多数 CLI |
| Git config `http.proxy` | `--global` / `--local` | 仅 Git |

> **关键认知**：四套配置互相独立，浏览器 OK 不代表 Git OK；定位时按上面五步法逐项核对，按方案表选最小副作用的修复方式。

### 关键代码

排查一行流（PowerShell）：

```powershell
# 一次性输出 Git 代理配置 + 环境变量代理 + WinINET 代理 + 直连 TCP 探测
git config --show-origin --get-regexp "http\..*proxy|https\..*proxy" ;
Get-ChildItem Env: | Where-Object { $_.Name -match '^(HTTP|HTTPS|ALL)_PROXY|NO_PROXY$' } | Format-Table -AutoSize ;
$s = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' ;
[pscustomobject]@{ ProxyEnable=$s.ProxyEnable; ProxyServer=$s.ProxyServer } | Format-List ;
Test-NetConnection github.com -Port 443 | Select-Object RemoteAddress,RemotePort,TcpTestSucceeded
```

临时让本次 git 操作走指定代理（不污染配置）：

```powershell
git -c http.proxy=http://127.0.0.1:<port> -c https.proxy=http://127.0.0.1:<port> <push|pull|ls-remote ...>
```

### 验证记录

- [2026-04-20] 初次记录。现场验证：浏览器与 `Invoke-WebRequest` 返回 200，但 `Test-NetConnection github.com:443` 失败、`git push` 报 `Recv failure: Connection was aborted`；定位到 WinINET `ProxyEnable=1, ProxyServer=http=127.0.0.1:7893;...`，使用 `git -c http.proxy=http://127.0.0.1:7893 push` 后推送成功。
