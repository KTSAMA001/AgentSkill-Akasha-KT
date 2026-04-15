import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from regenerate_index import (
    DATA_DIR,
    INDEX_FILE,
    TABLE_DIVIDER,
    TABLE_HEADER,
    build_metadata_pattern,
    generate_table_row,
    parse_markdown_file,
)


sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / DATA_DIR
INDEX_PATH = ROOT_DIR / INDEX_FILE
TAG_REGISTRY_PATH = ROOT_DIR / "references" / "tag-registry.md"
REQUIRED_METADATA_LABELS = ["标签", "来源", "收录日期", "状态", "可信度"]
REQUIRED_HEADINGS = ["概要", "验证记录"]
ALLOWED_STATUSES = {
    "✅ 已验证",
    "⚠️ 待验证",
    "📘 有效",
    "🔄 待更新",
    "📕 已过时",
    "❌ 已废弃",
    "🔬 实验性",
    "💡 构想中",
}
TYPE_DIMENSION = "type"
DOMAIN_DIMENSION = "domain"
FILENAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
TITLE_PATTERN = re.compile(r"^#\s+.+$", re.MULTILINE)
HEADING_TEMPLATE = r"^###\s+{heading}\s*$"
TAG_PATTERN = re.compile(r"#[^\s#]+")
MARKDOWN_LINK_PATTERN = re.compile(r"(!?)\[[^\]]*\]\(([^)]+)\)")
SEPARATOR_ROW_PATTERN = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$")
INDEX_FILE_SECTION_HEADER = "## 文件清单"


@dataclass
class Issue:
    severity: str
    scope: str
    message: str


@dataclass
class RecordInfo:
    filename: str
    path: Path
    title: str
    tags_line: str
    tags: list[str]
    status: str
    summary: str
    content: str


def parse_args():
    parser = argparse.ArgumentParser(description="Validate Akasha records without modifying files.")
    parser.add_argument(
        "--max-issues",
        type=int,
        default=100,
        help="Maximum number of issues to print before truncation.",
    )
    return parser.parse_args()


def split_markdown_row(line):
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    body = stripped.strip("|")
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", body)]


def parse_tag_registry():
    content = TAG_REGISTRY_PATH.read_text(encoding="utf-8")
    registry = {}
    for line in content.splitlines():
        if not line.startswith("|"):
            continue
        if SEPARATOR_ROW_PATTERN.match(line):
            continue
        cells = split_markdown_row(line)
        if len(cells) < 4:
            continue
        tag = cells[0]
        dimension = cells[3]
        if not tag.startswith("#"):
            continue
        registry[tag] = dimension
    return registry


def parse_tags(tags_line):
    return TAG_PATTERN.findall(tags_line)


def add_issue(issues, severity, scope, message):
    issues.append(Issue(severity=severity, scope=scope, message=message))


def check_required_metadata(content, filename, issues):
    for label in REQUIRED_METADATA_LABELS:
        pattern = build_metadata_pattern(label)
        if not pattern.search(content):
            add_issue(issues, "error", filename, f"缺少必填元数据字段：{label}")


def check_required_headings(content, filename, issues):
    if not TITLE_PATTERN.search(content):
        add_issue(issues, "error", filename, "缺少 H1 标题")

    for heading in REQUIRED_HEADINGS:
        pattern = re.compile(HEADING_TEMPLATE.format(heading=re.escape(heading)), re.MULTILINE)
        if not pattern.search(content):
            add_issue(issues, "error", filename, f"缺少必填章节：### {heading}")


def validate_tags(record, tag_registry, issues):
    if not record.tags:
        add_issue(issues, "error", record.filename, "未解析到任何标签")
        return

    if len(record.tags) < 2:
        add_issue(issues, "error", record.filename, "标签数量不足，至少需要 2 个标签")

    unknown_tags = [tag for tag in record.tags if tag not in tag_registry]
    for tag in unknown_tags:
        add_issue(issues, "error", record.filename, f"标签未注册：{tag}")

    registered_tags = [tag for tag in record.tags if tag in tag_registry]
    domain_count = sum(1 for tag in registered_tags if tag_registry[tag] == DOMAIN_DIMENSION)
    type_count = sum(1 for tag in registered_tags if tag_registry[tag] == TYPE_DIMENSION)

    if domain_count < 1:
        add_issue(issues, "error", record.filename, "至少需要 1 个领域标签（dimension=domain）")
    if type_count != 1:
        add_issue(issues, "error", record.filename, f"类型标签数量必须恰好为 1，当前为 {type_count}")


def validate_status(record, issues):
    if not record.status:
        add_issue(issues, "error", record.filename, "未解析到状态字段")
        return

    if record.status not in ALLOWED_STATUSES:
        add_issue(
            issues,
            "error",
            record.filename,
            f"状态字段不在固定枚举内：{record.status}",
        )


def is_external_target(target):
    lowered = target.lower()
    return lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("mailto:")


def is_anchor_target(target):
    return target.startswith("#")


def is_absolute_target(target):
    return bool(re.match(r"^[a-zA-Z]:[/\\]", target)) or target.startswith("/") or target.startswith("file://")


def validate_markdown_targets(record, issues):
    for _, raw_target in MARKDOWN_LINK_PATTERN.findall(record.content):
        target = raw_target.strip()
        if not target:
            continue

        link_path = target.split("#", 1)[0].strip()
        if not link_path or is_external_target(link_path) or is_anchor_target(link_path):
            continue

        if is_absolute_target(link_path):
            add_issue(issues, "error", record.filename, f"发现绝对路径引用：{link_path}")
            continue

        resolved_path = (record.path.parent / link_path).resolve()
        if not resolved_path.exists():
            add_issue(issues, "error", record.filename, f"引用目标不存在：{link_path}")


def load_record_info(path):
    content = path.read_text(encoding="utf-8")
    title, tags_line, status, summary, _ = parse_markdown_file(str(path))
    tags = parse_tags(tags_line)
    return RecordInfo(
        filename=path.name,
        path=path,
        title=title,
        tags_line=tags_line,
        tags=tags,
        status=status,
        summary=summary,
        content=content,
    )


def validate_records(tag_registry):
    issues = []
    records = {}

    for path in sorted(DATA_PATH.glob("*.md")):
        record = load_record_info(path)
        records[record.filename] = record

        if not FILENAME_PATTERN.match(record.filename):
            add_issue(issues, "error", record.filename, "文件名不符合 kebab-case 规范")

        check_required_metadata(record.content, record.filename, issues)
        check_required_headings(record.content, record.filename, issues)
        validate_tags(record, tag_registry, issues)
        validate_status(record, issues)
        validate_markdown_targets(record, issues)

    return records, issues


def extract_index_rows():
    content = INDEX_PATH.read_text(encoding="utf-8")
    if INDEX_FILE_SECTION_HEADER not in content:
        raise ValueError("INDEX.md 缺少 '## 文件清单' 区块")

    _, suffix = content.split(INDEX_FILE_SECTION_HEADER, 1)
    lines = suffix.splitlines()
    rows = []
    started = False

    for line in lines:
        if not started:
            if line.strip() == TABLE_HEADER:
                started = True
            continue

        if line.strip() == TABLE_DIVIDER:
            continue
        if not line.startswith("|"):
            break
        rows.append(line.strip())

    return rows


def parse_index_filename(row):
    match = re.search(r"\[([^\]]+\.md)\]\(\.\./data/[^)]+\)", row)
    return match.group(1) if match else None


def validate_index(records):
    issues = []
    actual_rows = extract_index_rows()
    actual_by_file = {}

    for row in actual_rows:
        filename = parse_index_filename(row)
        if not filename:
            add_issue(issues, "error", "INDEX.md", f"无法解析文件清单行：{row}")
            continue
        actual_by_file[filename] = row

    expected_by_file = {}
    for filename in sorted(records):
        record = records[filename]
        expected_by_file[filename] = generate_table_row(
            record.filename,
            record.tags_line,
            record.status,
            record.summary,
        )

    missing = sorted(set(expected_by_file) - set(actual_by_file))
    extra = sorted(set(actual_by_file) - set(expected_by_file))

    for filename in missing:
        add_issue(issues, "error", "INDEX.md", f"文件清单缺少记录：{filename}")
    for filename in extra:
        add_issue(issues, "error", "INDEX.md", f"文件清单存在多余记录：{filename}")

    for filename in sorted(set(expected_by_file) & set(actual_by_file)):
        if expected_by_file[filename] != actual_by_file[filename]:
            add_issue(issues, "error", "INDEX.md", f"文件清单行未同步最新记录：{filename}")

    return issues


def print_issues(issues, max_issues):
    if not issues:
        print("No issues found.")
        return

    print(f"Found {len(issues)} issue(s):")
    for issue in issues[:max_issues]:
        print(f"- [{issue.severity}] {issue.scope}: {issue.message}")

    if len(issues) > max_issues:
        print(f"... truncated {len(issues) - max_issues} additional issue(s).")


def main():
    args = parse_args()
    tag_registry = parse_tag_registry()
    all_issues = []

    if not tag_registry:
        add_issue(all_issues, "error", "tag-registry.md", "未解析到任何标签注册信息")

    records, record_issues = validate_records(tag_registry)
    index_issues = validate_index(records)
    all_issues.extend(record_issues)
    all_issues.extend(index_issues)

    print_issues(all_issues, args.max_issues)
    error_count = sum(1 for issue in all_issues if issue.severity == "error")
    warning_count = sum(1 for issue in all_issues if issue.severity == "warning")
    print(f"Summary: {error_count} error(s), {warning_count} warning(s).")

    raise SystemExit(1 if error_count else 0)


if __name__ == "__main__":
    main()