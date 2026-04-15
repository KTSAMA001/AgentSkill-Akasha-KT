import re
import sys
from pathlib import Path

from regenerate_index import DATA_DIR, INDEX_FILE, TABLE_HEADER, build_metadata_pattern


sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / DATA_DIR
INDEX_PATH = ROOT_DIR / INDEX_FILE
DATE_TODAY = "2026-04-15"
METADATA_ORDER = ["标签", "来源", "收录日期", "来源日期", "更新日期", "状态", "可信度", "适用版本"]
SECTION_PATTERN = re.compile(r"^###\s+(?P<name>.+?)\s*$", re.MULTILINE)
INDEX_ROW_PATTERN = re.compile(
    r"^\|\s*\[(?P<filename>[^\]]+\.md)\]\([^)]*\)\s*\|\s*(?P<tags>.*?)\s*\|\s*(?P<status>.*?)\s*\|\s*(?P<summary>.*?)\s*\|$"
)

STATUS_FIXES = {
    "⚠️ 待验证（待美术实际测试）": ("⚠️ 待验证", "原状态备注“待美术实际测试”已移入验证记录，等待美术实测。"),
    "📘有效": ("📘 有效", None),
    "⚠️ 部分解决（v4.13.2 仍有报告）": ("🔄 待更新", "原状态“部分解决（v4.13.2 仍有报告）”说明问题未完全收敛，暂按待更新处理。"),
    "⚠️ 待验证（MCP部分未完成）": ("⚠️ 待验证", "原状态备注“MCP部分未完成”已移入验证记录。"),
    "✅已验证": ("✅ 已验证", None),
    "⚠️待验证": ("⚠️ 待验证", None),
    "⚠️ 解决方案已验证，根因待查": ("🔄 待更新", "修复方案已验证，但根因仍待补充，因此调整为待更新。"),
    "💡 灵感记录": ("💡 构想中", "原状态“灵感记录”已按固定枚举归一到“构想中”。"),
    "✅ 已解决": ("✅ 已验证", "原状态“已解决”已按固定枚举归一到“已验证”。"),
    "✅ 已验证（二次深度修正）": ("✅ 已验证", "原状态附注“二次深度修正”已移入验证记录。"),
    "⚠️ 待验证（需根据 Unity 版本和 DOTS 版本 调整）": ("⚠️ 待验证", "原状态备注“需根据 Unity 版本和 DOTS 版本调整”已移入验证记录。"),
    "⚠️ 待验证（需根据 Unity 版本和 DOTS 版本调整）": ("⚠️ 待验证", "原状态备注“需根据 Unity 版本和 DOTS 版本调整”已移入验证记录。"),
}

TAGS_FIXES = {
    "amplify-shader-editor-architecture.md": "#unity #shader #graphics #architecture #urp",
    "claude-code-comprehensive-guide.md": "#claude-code #tools #reference",
    "claude-code-source-architecture.md": "#claude-code #mcp #architecture #agent-skills",
    "git-config-in-repo.md": "#git #docker #experience #credential",
    "git-merge-3way-file-not-in-base.md": "#git #experience",
    "idea-3d-girl-smart-furniture.md": "#design #idea #smart-furniture",
    "kira-framework-analysis.md": "#unity #csharp #architecture #ui #mvvm",
    "ktsama-bilibili-profile.md": "#design #reference #social #ktsama #bilibili",
    "li-comm-polling-to-event-driven.md": "#docker #architecture #astrbot #openclaw",
    "modified-renderdoc-wuwa-capture.md": "#graphics #windows #reference #renderdoc #anti-bot #hook #rendering #zhihu",
    "prefab-variant-generator-v4-toolkit.md": "#unity #tools #architecture #custom-editor",
    "unity-blendtree-audio-sync.md": "#unity #experience #animation #blend-tree #audio",
    "unity-framework-architecture.md": "#unity #csharp #architecture",
    "unity6-migration-guide.md": "#unity #shader #reference #urp #rendering #ecs",
    "vera-kt-dog-identity.md": "#design #reference #social #vera #identity",
    "vitepress-architecture-deep-dive.md": "#web #vitepress #architecture",
}

METADATA_FIXES = {
    "astrbot-plugin-file-upload-onebot.md": {
        "来源": "web_archive_mcp_v2 插件源码分析 + OneBot v11 API 文档",
        "可信度": "⭐⭐⭐⭐ (源码 + 官方文档交叉验证)",
    },
    "astrbot-plugin-llm-request-interceptor.md": {
        "来源": "AstrBot 插件源码分析 + AstrBot 事件钩子机制验证",
        "可信度": "⭐⭐⭐⭐ (源码结构分析)",
    },
    "claude-code-backend-models.md": {
        "来源": "Claude Code 官方文档 / 发布说明 / 实践验证",
    },
    "claude-code-fork-session.md": {
        "来源": "Claude Code 官方文档",
    },
    "claude-code-latest-features-2026.md": {
        "来源": "Claude Code 官方发布说明 / 官方文档",
    },
    "img-svg-css-color-filter.md": {
        "可信度": "⭐⭐⭐⭐ (实践验证)",
    },
    "vitepress-sidebar-highlight-padding.md": {
        "可信度": "⭐⭐⭐⭐ (实践验证)",
    },
    "vitepress-vpfeature-icon-structure.md": {
        "可信度": "⭐⭐⭐⭐ (实践验证)",
    },
}

HEADER_REPLACEMENTS = {
    "git-config-in-repo.md": (
        re.compile(r"\A# Git 配置跟随仓库持久化\n\n(?:.|\n)*?^## 问题场景\s*$", re.MULTILINE),
        "# Git 配置跟随仓库持久化\n\n"
        "**标签**：#git #docker #experience #credential\n"
        "**来源**：OpenClaw 容器环境实践\n"
        "**收录日期**：2026-03-09\n"
        "**来源日期**：2026-03-09\n"
        "**状态**：✅ 已验证\n"
        "**可信度**：⭐⭐⭐⭐ (实践验证)\n\n"
        "### 概要\n\n"
        "Docker 容器重建后，如果 Git 配置只写在 `~/.gitconfig`，会随容器销毁丢失。将配置写入仓库内 `.git/config` 可以让配置和挂载卷一起持久化。\n\n"
        "## 问题场景"
    ),
    "git-https-fail-switch-ssh.md": (
        re.compile(r"\A# Git HTTPS 拉取失败，改用 SSH 协议解决\n\n(?:.|\n)*?^\*\*问题/场景\*\*：\s*$", re.MULTILINE),
        "# Git HTTPS 拉取失败，改用 SSH 协议解决\n\n"
        "**标签**：#git #experience #pat #docker #credential\n"
        "**来源**：KTSAMA 实践经验\n"
        "**收录日期**：2026-01-30\n"
        "**来源日期**：2026-01-30\n"
        "**状态**：✅ 已验证\n"
        "**可信度**：⭐⭐⭐⭐ (实践验证)\n"
        "**适用版本**：Git 2.x+\n\n"
        "### 概要\n\n"
        "已存在仓库通过 HTTPS 拉取持续失败，但改为 SSH 远程地址后可立即恢复。该类问题通常与网络链路、代理干扰或认证通道稳定性有关，而不是仓库内容本身损坏。\n\n"
        "**问题/场景**："
    ),
    "git-object-corrupt-repair.md": (
        re.compile(r"\A# Git 对象损坏（loose object corrupt）修复 \{#git-object-corrupt\}\n\n(?:.|\n)*?^\*\*问题/场景\*\*：\s*$", re.MULTILINE),
        "# Git 对象损坏（loose object corrupt）修复 {#git-object-corrupt}\n\n"
        "**标签**：#git #docker #experience #troubleshooting #credential\n"
        "**来源**：KTSAMA 实践经验\n"
        "**收录日期**：2026-02-05\n"
        "**来源日期**：2026-02-05\n"
        "**状态**：🔄 待更新\n"
        "**可信度**：⭐⭐⭐ (修复方案已验证，根因未确认)\n"
        "**适用版本**：Git 2.x+\n\n"
        "### 概要\n\n"
        "当 Git loose object 损坏时，可以从正常仓库重新写回缺失对象完成修复；但本案例的真实触发根因尚未确认，因此该记录仍需继续更新。\n\n"
        "**问题/场景**："
    ),
    "macos-git-osxkeychain-path.md": (
        re.compile(r"\A# macOS Git osxkeychain Credential Helper 路径问题 \{#osxkeychain-path\}\n\n(?:.|\n)*?^\*\*问题/场景\*\*：\s*$", re.MULTILINE),
        "# macOS Git osxkeychain Credential Helper 路径问题 {#osxkeychain-path}\n\n"
        "**标签**：#macos #git #experience #pat #credential\n"
        "**来源**：KTSAMA 实践经验\n"
        "**收录日期**：2026-02-05\n"
        "**来源日期**：2026-02-05\n"
        "**状态**：✅ 已验证\n"
        "**可信度**：⭐⭐⭐⭐ (实践验证)\n"
        "**适用版本**：Git 2.x+ (Homebrew)\n\n"
        "### 概要\n\n"
        "Homebrew 安装的 Git 在 macOS 上可能找不到 `git-credential-osxkeychain`，原因不是功能缺失，而是 helper 不在 PATH。将 `credential.helper` 配置为完整可执行路径即可恢复认证。\n\n"
        "**问题/场景**："
    ),
}

INLINE_TEXT_REPLACEMENTS = {
    "astrbot-plugin-file-upload-onebot.md": [
        (
            "- [web_archive_mcp_v2 插件源码](/AstrBot/data/plugins/web_archive_mcp_v2/main.py)",
            "- web_archive_mcp_v2 插件源码（本地插件路径：AstrBot/data/plugins/web_archive_mcp_v2/main.py）",
        ),
    ],
    "dotnet-cross-platform-compile-verify.md": [
        (
            "- [.NET SDK 环境部署](./dotnet-sdk-setup.md) - 环境安装步骤",
            "- .NET SDK 环境部署 - 相关记录待补录，当前先保留主题说明",
        ),
        (
            "- [Avalonia UI 跨平台开发](./avalonia-ui-cross-platform.md) - 框架使用指南",
            "- Avalonia UI 跨平台开发 - 相关记录待补录，当前先保留主题说明",
        ),
    ],
}


def load_index_summaries():
    content = INDEX_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()
    summaries = {}
    in_table = False

    for line in lines:
        if not in_table:
            if line.strip() == TABLE_HEADER:
                in_table = True
            continue

        if not line.startswith("|"):
            break
        if line.strip() == TABLE_HEADER or line.startswith("|------"):
            continue

        match = INDEX_ROW_PATTERN.match(line.strip())
        if not match:
            continue
        filename = match.group("filename")
        summary = match.group("summary").replace("\\|", "|").strip()
        summaries[filename] = summary

    return summaries


def metadata_pattern(label):
    return build_metadata_pattern(label)


def normalize_required_headings(content):
    content = re.sub(r"^##+\s*概要\s*$", "### 概要", content, flags=re.MULTILINE)
    content = re.sub(r"^##+\s*验证记录\s*$", "### 验证记录", content, flags=re.MULTILINE)
    content = re.sub(r"^\*\*验证记录\*\*[:：]\s*$", "### 验证记录", content, flags=re.MULTILINE)
    return content


def find_title_end(lines):
    for index, line in enumerate(lines):
        if line.startswith("# "):
            return index + 1
    return 0


def find_metadata_end(lines):
    index = find_title_end(lines)
    saw_metadata = False
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("**") and "：" in stripped:
            saw_metadata = True
            index += 1
            continue
        break
    return index if saw_metadata else find_title_end(lines)


def insert_summary_section(content, summary):
    if re.search(r"^###\s+概要\s*$", content, re.MULTILINE):
        return content

    lines = content.splitlines()
    insert_at = find_metadata_end(lines)
    block = ["", "### 概要", "", summary.strip(), ""]
    new_lines = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")


def append_to_validation_section(content, note):
    if not note:
        return content

    marker = "### 验证记录"
    if marker not in content:
        content = ensure_validation_section(content, [])

    if note in content:
        return content

    lines = content.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == marker)
    insert_at = len(lines)
    for index in range(start + 1, len(lines)):
        if index > start + 1 and lines[index].startswith("### "):
            insert_at = index
            break

    note_line = f"- [{DATE_TODAY}] {note}"
    new_lines = lines[:insert_at]
    if new_lines and new_lines[-1].strip():
        new_lines.append("")
    new_lines.append(note_line)
    new_lines.extend(lines[insert_at:])
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")


def ensure_validation_section(content, notes):
    if re.search(r"^###\s+验证记录\s*$", content, re.MULTILINE):
        for note in notes:
            content = append_to_validation_section(content, note)
        return content

    block_lines = ["", "### 验证记录", ""]
    for note in notes:
        block_lines.append(f"- [{DATE_TODAY}] {note}")
    if not notes:
        block_lines.append(f"- [{DATE_TODAY}] 结构修复：补齐模板必填章节，未改动原结论。")

    stripped = content.rstrip()
    if stripped.endswith("---"):
        stripped = stripped[:-3].rstrip()

    return stripped + "\n\n" + "\n".join(block_lines) + "\n"


def replace_metadata_value(content, label, value):
    pattern = metadata_pattern(label)
    replacement = f"**{label}**：{value}"
    if pattern.search(content):
        return pattern.sub(replacement, content, count=1)

    lines = content.splitlines()
    title_end = find_title_end(lines)
    insert_at = title_end
    for ordered_label in METADATA_ORDER:
        current_pattern = metadata_pattern(ordered_label)
        for index, line in enumerate(lines):
            if current_pattern.match(line):
                if METADATA_ORDER.index(ordered_label) <= METADATA_ORDER.index(label):
                    insert_at = index + 1
                break

    lines.insert(insert_at, replacement)
    return "\n".join(lines) + ("\n" if content.endswith("\n") else "")


def apply_header_replacement(filename, content):
    if filename not in HEADER_REPLACEMENTS:
        return content
    pattern, replacement = HEADER_REPLACEMENTS[filename]
    return pattern.sub(replacement, content, count=1)


def apply_inline_replacements(filename, content):
    for old, new in INLINE_TEXT_REPLACEMENTS.get(filename, []):
        content = content.replace(old, new)
    return content


def normalize_status(content):
    pattern = metadata_pattern("状态")
    match = pattern.search(content)
    if not match:
        return content, None

    old_status = match.group(1).strip()
    new_status, note = STATUS_FIXES.get(old_status, (old_status, None))
    if new_status != old_status:
        content = pattern.sub(f"**状态**：{new_status}", content, count=1)
    return content, note


def update_tags(filename, content):
    if filename not in TAGS_FIXES:
        return content
    pattern = metadata_pattern("标签")
    replacement = f"**标签**：{TAGS_FIXES[filename]}"
    if pattern.search(content):
        return pattern.sub(replacement, content, count=1)
    return replace_metadata_value(content, "标签", TAGS_FIXES[filename])


def main():
    summaries = load_index_summaries()
    changed_files = []

    for path in sorted(DATA_PATH.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        content = original

        content = apply_header_replacement(path.name, content)
        content = apply_inline_replacements(path.name, content)
        content = normalize_required_headings(content)
        content = update_tags(path.name, content)

        for label, value in METADATA_FIXES.get(path.name, {}).items():
            content = replace_metadata_value(content, label, value)

        content, status_note = normalize_status(content)

        summary = summaries.get(path.name)
        if summary:
            content = insert_summary_section(content, summary)

        validation_notes = []
        if status_note:
            validation_notes.append(status_note)

        if not re.search(r"^###\s+验证记录\s*$", content, re.MULTILINE):
            validation_notes.insert(0, "结构修复：补齐模板必填章节，未改动原结论。")

        content = ensure_validation_section(content, validation_notes)

        if content != original:
            path.write_text(content, encoding="utf-8")
            changed_files.append(path.name)

    print(f"Updated {len(changed_files)} files.")
    for filename in changed_files:
        print(f"- {filename}")


if __name__ == "__main__":
    main()