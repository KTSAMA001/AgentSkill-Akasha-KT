# .NET 跨平台编译环境验证

**标签**：#csharp #dotnet #tools #experience
**来源**：实践总结 - OpenClaw 容器环境部署验证
**收录日期**：2026-02-27
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实地部署验证)
**适用版本**：.NET SDK 8.0+

### 概要
验证在 Linux arm64 容器中部署的 .NET SDK 能否成功编译 macOS arm64 跨平台应用。

### 内容

#### 验证目标

确认 KT 的 .NET/C# 开发环境部署成功后，具备以下能力：
- ✅ 在 Linux arm64 容器中编译 macOS arm64 应用
- ✅ 使用 Avalonia UI 跨平台框架
- ✅ 自包含发布（self-contained）
- ✅ 输出可直接在 macOS 上运行的应用

#### 测试项目：MdViewer

一个简单的 Markdown 实时预览工具，用于验证编译流程：
- 双栏布局（编辑 + 预览）
- Markdig 解析 Markdown
- Avalonia UI 渲染界面
- 导出 HTML 功能

#### 编译流程

```bash
# 1. 还原依赖
dotnet restore

# 2. 编译 macOS arm64 自包含版本
dotnet publish -c Release -r osx-arm64 --self-contained true -o publish/macos

# 3. 打包
tar -czvf MdViewer-macos-arm64.tar.gz macos/
```

#### macOS 运行说明

```bash
# 解压
tar -xzf MdViewer-macos-arm64.tar.gz
cd macos

# 首次运行需要签名（自动化脚本）
./run.sh

# 或手动签名
codesign --deep --force --sign - ./MdViewer
xattr -cr .
./MdViewer
```

### 关键代码

**项目配置** (MdViewer.csproj)：
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <BuiltInComInteropSupport>true</BuiltInComInteropSupport>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Avalonia" Version="11.2.2" />
    <PackageReference Include="Avalonia.Desktop" Version="11.2.2" />
    <PackageReference Include="Markdig" Version="0.38.0" />
  </ItemGroup>
</Project>
```

### 注意事项

1. **代码签名**：macOS 对未签名应用会阻止运行，需执行 `codesign --sign -`
2. **隔离属性**：使用 `xattr -cr .` 移除 quarantine 属性
3. **自包含发布**：`--self-contained true` 确保不依赖目标机器上的 .NET 运行时
4. **Avalonia 版本**：11.x 版本支持 .NET 8，注意包版本兼容性

### 验证记录
- [2026-02-27] 初次验证，来源：OpenClaw 容器环境部署测试
  - 编译环境：Debian 12 arm64 + .NET SDK 8.0.403
  - 目标平台：macOS arm64
  - 结果：✅ 成功编译并运行

### 相关记录

- .NET SDK 环境部署 - 相关记录待补录，当前先保留主题说明
- Avalonia UI 跨平台开发 - 相关记录待补录，当前先保留主题说明

### 结论

**环境验证通过** ✅

KT 的 .NET 开发环境已具备完整的跨平台编译能力，可以用于：
- Unity 工具开发（编辑器扩展、自动化工具）
- 跨平台桌面应用开发
- CI/CD自动化编译流程
