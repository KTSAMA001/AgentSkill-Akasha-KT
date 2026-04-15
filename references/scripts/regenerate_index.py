import os
import re
import sys

# Windows 控制台默认编码为 GBK，无法输出 emoji（✅📘📕等），强制 UTF-8
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DATA_DIR = "data"
INDEX_FILE = "references/INDEX.md"
TABLE_HEADER = "| 文件 | 标签 | 状态 | 简述 |"
TABLE_DIVIDER = "|------|------|------|------|"
STATUS_MARKERS = ["✅", "⚠️", "📘", "🔄", "📕", "❌", "🔬", "💡"]


def build_metadata_pattern(label):
    parts = [re.escape(char) for char in label]
    text = r"\s*".join(parts)
    return re.compile(rf'\*\*\s*{text}\s*\*\*\s*[:：]\s*(.*)')


TITLE_PATTERN = re.compile(r'^#\s+(.*)$')
SUMMARY_HEADING_PATTERN = re.compile(r'^###\s+概要\s*$')
METADATA_PATTERNS = {
    "tags": build_metadata_pattern("标签"),
    "status": build_metadata_pattern("状态"),
}

def parse_markdown_file(filepath):
    """
    Parses a markdown file to extract metadata.
    Returns: title, tags, status, summary, warnings
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    warnings = []

    # Extract Title (First H1)
    title = os.path.basename(filepath)
    for line in lines:
        match = TITLE_PATTERN.match(line.strip())
        if match:
            title = match.group(1).strip()
            break

    # Extract Metadata
    tags = ""
    status = ""
    summary = ""

    tags_match = METADATA_PATTERNS["tags"].search(content)
    if tags_match:
        tags = tags_match.group(1).strip()
    else:
        warnings.append("missing 标签 metadata")

    status_match = METADATA_PATTERNS["status"].search(content)
    if status_match:
        status = status_match.group(1).strip()
    else:
        warnings.append("missing 状态 metadata")

    if status and not any(status.startswith(marker) for marker in STATUS_MARKERS):
        warnings.append(f"unknown status marker: {status}")

    summary = extract_summary(lines)
    if not summary:
        summary = title
        warnings.append("missing 概要 section, fallback to title")

    return title, tags, status, summary, warnings


def extract_summary(lines):
    in_summary = False
    summary_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not in_summary:
            if SUMMARY_HEADING_PATTERN.match(line):
                in_summary = True
            continue

        if line.startswith('#'):
            break
        if not line:
            if summary_lines:
                break
            continue

        summary_lines.append(line)

    if not summary_lines:
        return ""

    summary = " ".join(summary_lines)
    summary = summary.replace("|", "\\|")
    return re.sub(r'\s+', ' ', summary).strip()

def generate_table_row(filename, tags, status, summary):
    status = normalize_status(status)
    link = f"[{filename}](../{DATA_DIR}/{filename})"
    return f"| {link} | {tags} | {status} | {summary} |"


def normalize_status(status):
    if not status:
        return status

    text = status.strip()
    for marker in STATUS_MARKERS:
        if text.startswith(marker):
            remain = text[len(marker):].strip()
            return f"{marker} {remain}" if remain else marker
    return text


def replace_table(index_content, new_table):
    header_marker = "## 文件清单"

    if header_marker not in index_content:
        raise ValueError("Could not find '## 文件清单' section.")

    prefix, suffix = index_content.split(header_marker, 1)
    section_prefix = prefix + header_marker
    table_start = suffix.find(TABLE_HEADER)

    if table_start == -1:
        return section_prefix + "\n\n" + new_table + "\n"

    before_table = suffix[:table_start]
    table_and_rest = suffix[table_start:].splitlines()
    rest_start = 0

    for index, line in enumerate(table_and_rest):
        if index == 0 and line == TABLE_HEADER:
            rest_start = index + 1
            continue
        if index == 1 and line == TABLE_DIVIDER:
            rest_start = index + 1
            continue
        if index >= 2 and line.startswith('|'):
            rest_start = index + 1
            continue
        break

    rest = "\n".join(table_and_rest[rest_start:]).lstrip("\n")
    rebuilt = section_prefix + before_table + new_table + "\n"
    if rest:
        rebuilt += "\n" + rest
        if not rebuilt.endswith("\n"):
            rebuilt += "\n"
    return rebuilt

def main():
    # 1. Get List of Files
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.md')]
    files.sort()

    table_rows = []
    warnings = []

    print(f"Scanning {len(files)} files...")

    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        try:
            title, tags, status, summary, file_warnings = parse_markdown_file(filepath)
            row = generate_table_row(filename, tags, status, summary)
            table_rows.append(row)
            for warning in file_warnings:
                warnings.append(f"{filename}: {warning}")
        except Exception as e:
            print(f"Error parsing {filename}: {e}")

    # 2. Read INDEX.md
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index_content = f.read()

    # 3. Replace only the file table while preserving the rest of INDEX.md.
    new_table = f"{TABLE_HEADER}\n{TABLE_DIVIDER}\n" + "\n".join(table_rows)
    final_content = replace_table(index_content, new_table)

    # 4. Write Back
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"Successfully updated {INDEX_FILE} with {len(table_rows)} entries.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

if __name__ == "__main__":
    main()
