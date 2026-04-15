# Markdown to Word 转换器实现详解

**标签**：#python #tools #experience #docx #markdown
**来源**：实践总结
**收录日期**：2026-03-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐

### 概要
基于 Python 的 Markdown 转 Word (.docx) 文档转换器，支持代码语法高亮、Mermaid/PlantUML 图表渲染、表格转换、图片嵌入等功能。核心使用 `python-docx` + `markdown` + `Pygments` + `BeautifulSoup4` 技术栈。

### 技术架构

```
md_to_word_converter/
├── main.py            # 入口文件，依赖检查 + GUI 启动
├── converter.py       # 核心转换引擎（933行）
├── gui.py             # tkinter + ttkbootstrap GUI
├── requirements.txt   # 依赖清单
└── example.md         # 示例文件
```

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| python-docx | >=0.8.11 | 生成 Word 文档 |
| markdown | >=3.4 | 解析 Markdown 为 HTML |
| beautifulsoup4 | >=4.12 | 解析 HTML DOM 结构 |
| Pygments | >=2.16 | 代码语法高亮 |
| requests | >=2.31 | 网络请求（图片/图表下载） |
| ttkbootstrap | >=1.10 | 现代化 GUI 主题 |
| Pillow | 可选 | 图片智能尺寸计算 |

### 转换流程

```python
# 命令行调用方式
from converter import MarkdownToWordConverter

converter = MarkdownToWordConverter()
output = converter.convert('input.md', 'output.docx')
```

内部流程：
1. **读取 MD** → 去除 YAML frontmatter
2. **MD → HTML** → 使用 `markdown.markdown()` + 扩展
3. **HTML → DOM** → BeautifulSoup 解析
4. **DOM → Word** → 遍历元素，逐个转换为 docx 元素

### 关键实现细节

#### 1. Markdown 扩展配置

```python
extensions = [
    'tables',           # GFM 表格
    'fenced_code',      # 围栏代码块
    'sane_lists',       # 改进的列表
    'attr_list',        # 属性列表
    'toc',              # 目录生成
    'md_in_html',       # HTML 内嵌 MD
]
ext_cfg = {
    'fenced_code': {'lang_prefix': 'language-'},
}
html = markdown.markdown(text, extensions=extensions, extension_configs=ext_cfg)
```

#### 2. 代码语法高亮（Pygments）

```python
# 构建颜色映射表
def _build_color_map(style_name='friendly'):
    style = get_style_by_name(style_name)
    color_map = {}
    for token_type, token_style in style:
        color_map[token_type] = {
            'color': token_style['color'],
            'bold': token_style['bold'],
            'italic': token_style['italic'],
        }
    return color_map, style.background_color

# 词法分析 + 逐 token 渲染
lexer = get_lexer_by_name(lang)  # 根据语言获取词法分析器
tokens = list(lexer.get_tokens(code_text))
# 每个 token 对应一个带颜色/样式的 run
```

#### 3. Word 样式配置

```python
# 页边距（A4）
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.0)
section.right_margin = Cm(3.0)

# 标题样式（分层配色）
heading_cfg = {
    1: {'size': 26, 'color': (0x1A, 0x3A, 0x5C), 'before': 18, 'after': 8},
    2: {'size': 22, 'color': (0x2E, 0x5F, 0x8A), 'before': 14, 'after': 6},
    3: {'size': 18, 'color': (0x3A, 0x6B, 0x8C), 'before': 10, 'after': 4},
    # ...
}

# 中文字体 fallback
rfonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
```

#### 4. 图表渲染（Mermaid / PlantUML）

```python
# Mermaid - 通过 mermaid.ink API
encoded = base64.urlsafe_b64encode(code.encode('utf-8')).decode('utf-8')
url = f"https://mermaid.ink/img/{encoded}"
resp = requests.get(url, timeout=30)
# 下载 PNG → 嵌入 Word

# PlantUML - 通过 plantuml.com API
hex_str = binascii.hexlify(code.encode('utf-8')).decode('utf-8')
url = f"http://www.plantuml.com/plantuml/png/~h{hex_str}"
resp = requests.get(url, timeout=30)
```

#### 5. 表格处理

```python
# 自动计算列宽（按内容比例）
def _calc_col_widths(rows_data, n_cols):
    available = int(15.0 * 567)  # A4 可用宽度（twips）
    min_w, max_w = int(1.5 * 567), int(8.0 * 567)

    # 按最大字符数分配
    max_chars = [max(len(row[j]) for row in rows_data) for j in range(n_cols)]
    total_chars = sum(max_chars)
    widths = [max(min_w, min(max_w, int(available * c / total_chars))) for c in max_chars]
    return widths

# 表头灰色背景 + 斑马纹
if i < header_count:
    shd.set(qn('w:fill'), 'E8EDF2')  # 表头
elif (i - header_count) % 2 == 1:
    shd.set(qn('w:fill'), 'F5F8FC')  # 奇数行
```

#### 6. 图片处理

```python
def _calculate_image_width(self, img_path: str) -> int:
    max_width_inches = 5.75   # A4 减去边距
    max_height_inches = 7.0

    # 使用 Pillow 读取真实尺寸
    with PILImage.open(img_path) as img:
        w_px, h_px = img.size
        dpi = img.info.get('dpi', (96, 96))
        # 按比例缩放
        if w_in > max_width_inches:
            scale = max_width_inches / w_in
            w_in, h_in = w_in * scale, h_in * scale
        return Inches(w_in)

# 图片来源支持
# 1. Data URI: data:image/png;base64,...
# 2. 远程 URL: https://...
# 3. 本地相对路径（相对于 MD 文件目录）
# 4. 本地绝对路径
```

#### 7. 超链接实现

```python
def _add_hyperlink(self, paragraph, el, bold=False, italic=False):
    url = el.get('href', '')
    r_id = paragraph.part.relate_to(url, HYPERLINK_REL, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    # 添加蓝色 + 下划线样式
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    c_el = OxmlElement('w:color')
    c_el.set(qn('w:val'), '0563C1')  # Word 默认链接蓝
    u_el = OxmlElement('w:u')
    u_el.set(qn('w:val'), 'single')
    # ...
```

### 支持的 Markdown 元素

| 元素 | 实现方式 | 注意点 |
|------|----------|--------|
| 标题 (h1-h6) | `doc.add_heading()` | H1 带底部边框 |
| 加粗/斜体/删除线 | `run.bold/italic/strike` | 递归处理嵌套 |
| 行内代码 | `InlineCode` 字符样式 | 深红色 Consolas |
| 代码块 | Pygments 语法高亮 | 左边框 + 背景色 |
| 有序/无序列表 | 手动渲染 | 支持嵌套，用 Unicode 符号 |
| 表格 | `doc.add_table()` | 自动列宽 + 斑马纹 |
| 引用块 | `BlockQuote` 样式 | 左侧蓝色竖线 |
| 图片 | `run.add_picture()` | 智能尺寸 + 居中 |
| 超链接 | `w:hyperlink` XML | 外部关系 + 蓝色下划线 |
| 水平分割线 | 底部边框 | 灰色细线 |
| Mermaid 图表 | mermaid.ink API | 渲染为 PNG 嵌入 |
| PlantUML 图表 | plantuml.com API | 渲染为 PNG 嵌入 |

### 配置选项

```python
DEFAULT_OPTIONS = {
    'first_line_indent': True,        # 首行缩进 0.74cm
    'heading_numbering': False,       # 标题自动编号
    'page_numbers': True,             # 页脚页码
    'alternating_table_rows': True,   # 表格斑马纹
}

# 使用
converter = MarkdownToWordConverter(options={
    'heading_numbering': True,
    'first_line_indent': False,
})
```

### 坑点与注意事项

1. **中文显示**：必须设置 `w:eastAsia` 字体，否则 Word 会用宋体 fallback
2. **图片路径**：相对路径基于 MD 文件目录（`self.md_dir`），非当前工作目录
3. **临时目录**：远程图片/图表下载到 `tempfile.TemporaryDirectory()`，避免污染
4. **YAML Frontmatter**：正则 `^---\s*\n.*?\n---\s*\n` 去除
5. **代码块空行**：空行需添加空格 ` ` 否则 Word 可能丢失段落
6. **图表超时**：Mermaid/PlantUML API 设置 30s 超时，失败时回退到纯文本
7. **Pillow 可选**：无 Pillow 时图片固定 5 英寸宽

### 扩展建议

- **自定义样式**：修改 `_setup_styles()` 中的颜色/字体配置
- **新增元素**：在 `_process_element()` 中添加分派逻辑
- **图表本地渲染**：可用 `mmdc` (mermaid-cli) 或 `plantuml.jar` 本地渲染
- **批量转换**：遍历目录，调用 `converter.convert()` 即可

### 参考链接

- [python-docx 文档](https://python-docx.readthedocs.io/)
- [Python-Markdown 扩展](https://python-markdown.github.io/extensions/)
- [Pygments 词法分析器](https://pygments.org/docs/lexers/)
- [mermaid.ink API](https://mermaid.ink/)
- [PlantUML API](https://plantuml.com/zh/)

### 验证记录
- [2026-03-13] 初次记录，基于项目源码分析
- [2026-03-13] 实际转换测试成功，输出 99KB docx 文件
