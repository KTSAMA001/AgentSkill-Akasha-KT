import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class RecordMeta:
    filename: str
    title: str
    tags_text: str
    tags: List[str]
    status: str
    summary: str


def detect_skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def extract_first_h1(content: str, default: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else default


def extract_metadata_line(content: str, key: str) -> str:
    pattern = rf"\*\*{re.escape(key)}\*\*\s*[:：]\s*(.+)"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else ""


def extract_summary(content: str) -> str:
    inline_summary = extract_metadata_line(content, "概要")
    if inline_summary:
        return inline_summary

    section_match = re.search(r"^#{2,3}\s*概要\s*$", content, re.MULTILINE)
    if not section_match:
        return ""

    tail = content[section_match.end():]
    lines = [line.strip() for line in tail.splitlines()]
    for line in lines:
        if not line:
            continue
        if line.startswith("#"):
            break
        return line
    return ""


def normalize_tags(tags_text: str) -> List[str]:
    return [tag.lower() for tag in re.findall(r"#([A-Za-z0-9_\-]+)", tags_text)]


def parse_record(filepath: Path) -> RecordMeta:
    content = filepath.read_text(encoding="utf-8")
    title = extract_first_h1(content, filepath.stem)
    tags_text = extract_metadata_line(content, "标签")
    status = extract_metadata_line(content, "状态")
    summary = extract_summary(content)
    tags = normalize_tags(tags_text)
    return RecordMeta(
        filename=filepath.name,
        title=title,
        tags_text=tags_text,
        tags=tags,
        status=status,
        summary=summary,
    )


def load_records(data_dir: Path) -> List[RecordMeta]:
    records: List[RecordMeta] = []
    for file_path in sorted(data_dir.glob("*.md")):
        try:
            records.append(parse_record(file_path))
        except Exception as ex:
            print(f"[WARN] 跳过 {file_path.name}: {ex}")
    return records


def contains_any_keyword(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def filter_records(records: List[RecordMeta], tags: List[str], keywords: List[str], status: str) -> List[RecordMeta]:
    normalized_tags = [tag.lower().lstrip("#") for tag in tags]
    normalized_status = status.strip()

    filtered: List[RecordMeta] = []
    for record in records:
        if normalized_tags and not any(tag in record.tags for tag in normalized_tags):
            continue

        if keywords:
            haystack = " ".join([record.filename, record.title, record.summary])
            if not contains_any_keyword(haystack, keywords):
                continue

        if normalized_status and normalized_status not in record.status:
            continue

        filtered.append(record)

    return filtered


def print_records(records: List[RecordMeta], limit: int) -> None:
    if not records:
        print("未找到匹配记录")
        return

    result = records[:limit]
    print(f"命中 {len(records)} 条，展示前 {len(result)} 条：")
    print("文件名 | 标签 | 状态 | 标题")
    print("---|---|---|---")
    for record in result:
        print(f"{record.filename} | {record.tags_text} | {record.status} | {record.title}")


def print_tags(records: List[RecordMeta]) -> None:
    counter = {}
    for record in records:
        for tag in record.tags:
            counter[tag] = counter.get(tag, 0) + 1

    if not counter:
        print("未发现任何标签")
        return

    print(f"标签总数：{len(counter)}")
    for tag, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        print(f"#{tag}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Akasha-KT 记录元数据搜索工具")
    parser.add_argument("--tags", nargs="*", default=[], help="按标签过滤（OR 逻辑），可不带 #")
    parser.add_argument("--keywords", nargs="*", default=[], help="按关键词过滤标题/概要/文件名（OR 逻辑）")
    parser.add_argument("--status", default="", help="按状态过滤，例如 ✅ 或 📘")
    parser.add_argument("--limit", type=int, default=20, help="最大展示条数，默认 20")
    parser.add_argument("--list-tags", action="store_true", help="列出所有标签及记录数")
    parser.add_argument("--list-all", action="store_true", help="列出所有记录")
    parser.add_argument("--deep", action="store_true", help="预留：全文搜索（当前未实现）")
    args = parser.parse_args()

    if args.deep:
        print("[INFO] --deep 全文搜索暂未实现，当前仅支持元数据搜索。")

    skill_root = detect_skill_root()
    data_dir = skill_root / "data"
    if not data_dir.exists():
        raise FileNotFoundError(f"未找到 data 目录: {data_dir}")

    records = load_records(data_dir)

    if args.list_tags:
        print_tags(records)
        return

    if args.list_all:
        print_records(records, args.limit if args.limit > 0 else len(records))
        return

    has_search_filter = bool(args.tags or args.keywords or args.status)
    if not has_search_filter:
        parser.print_help()
        return

    filtered = filter_records(records, args.tags, args.keywords, args.status)
    display_limit = args.limit if args.limit > 0 else len(filtered)
    print_records(filtered, display_limit)


if __name__ == "__main__":
    main()