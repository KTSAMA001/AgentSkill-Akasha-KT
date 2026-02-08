import os
import re

DATA_DIR = "data"
INDEX_FILE = "references/INDEX.md"

def parse_markdown_file(filepath):
    """
    Parses a markdown file to extract metadata.
    Returns: title, tags, status, description
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    
    # Extract Title (First H1)
    title = os.path.basename(filepath) # Default
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break
            
    # Extract Metadata
    tags = ""
    status = ""
    
    # Simple regex for metadata
    # **标签**：#tags
    tags_match = re.search(r'\*\*标签\*\*：(.*)', content)
    if tags_match:
        tags = tags_match.group(1).strip()
        
    # **状态**：✅ ...
    status_match = re.search(r'\*\*状态\*\*：(.*)', content)
    if status_match:
        status = status_match.group(1).strip()
        
    return title, tags, status

def generate_table_row(filename, title, tags, status):
    link = f"[{filename}](../{DATA_DIR}/{filename})"
    # Format: | File Link | Tags | Status | Description |
    # Note: The current INDEX.md uses a slightly weird format "：#tags" in the column?
    # Let's clean it up.
    
    # Clean status to just the icon and short text if possible? 
    # The current one has "：✅ 已验证". 
    # I will just put the text.
    
    return f"| {link} | {tags} | {status} | {title} |"

def main():
    # 1. Get List of Files
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.md')]
    files.sort()
    
    table_rows = []
    
    print(f"Scanning {len(files)} files...")
    
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        try:
            title, tags, status = parse_markdown_file(filepath)
            row = generate_table_row(filename, title, tags, status)
            table_rows.append(row)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            
    # 2. Read INDEX.md
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index_content = f.read()
        
    # 3. Find the Table Section
    # We look for "## 文件清单" and the table header.
    header_marker = "## 文件清单"
    table_header = "| 文件 | 标签 | 状态 | 简述 |"
    table_divider = "|------|------|------|------|"
    
    if header_marker not in index_content:
        print("Could not find '## 文件清单' section.")
        return

    # Split content
    parts = index_content.split(header_marker)
    pre_table_content = parts[0] + header_marker + "\n\n"
    
    # We need to construct the new content.
    # The part after "## 文件清单" might contain other text before the table?
    # In the current file, it seems the table is right after.
    
    new_table = f"{table_header}\n{table_divider}\n" + "\n".join(table_rows)
    
    # Reassemble. We discard the old table.
    # Assuming the table is the last thing or we just replace the section.
    # Let's try to be smart. Find where the table starts and ends.
    # But replacing everything after "## 文件清单" is easiest if it's the last section.
    # Let's check if there's anything after.
    # In the read_file output, "## 文件清单" is the last section visible.
    
    final_content = pre_table_content + new_table + "\n"
    
    # 4. Write Back
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"Successfully updated {INDEX_FILE} with {len(table_rows)} entries.")

if __name__ == "__main__":
    main()
