# python-docx Emoji 显示问题解决方案

**标签**：#python #docx #experience #font #unicode
**来源**：实践总结 + 在线研究
**收录日期**：2026-03-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：python-docx 0.8.11+

### 概要
解决 python-docx 生成的 Word 文档中 emoji 显示为方框或方框带问号的问题。根因是 `run.font.name` 只设置 Word XML 的 `w:ascii` 属性，而 emoji 字符（Unicode 补充平面，code point > 0xFFFF）需要通过 `w:hAnsi` 属性指定字体才能正确渲染。

### 问题描述

使用 python-docx 生成包含 emoji 的 Word 文档时：
- **症状 1**：emoji 显示为方框带问号（如 `□?`）
- **症状 2**：emoji 显示为空白方框（如 `□`）
- **症状 3**：部分 emoji 正常，部分异常

### 根因分析

#### Word XML 字体属性机制

Word 的 `w:rFonts` 元素包含多个字体属性：

| 属性 | 用途 | 字符范围 |
|------|------|----------|
| `w:ascii` | ASCII 字符 | 0x00-0x7F |
| `w:hAnsi` | 高 ANSI + catch-all | 0x80-0xFF 及其他 |
| `w:eastAsia` | 东亚字符 (CJK) | 中日韩文字 |
| `w:cs` | 复杂脚本 | 阿拉伯语、希伯来语等 |

**关键发现**：python-docx 的 `run.font.name = 'xxx'` 只设置 `w:ascii` 属性，不设置其他属性。

#### Emoji 字符特性

- Emoji 位于 Unicode **补充平面**（Supplementary Multilingual Plane）
- Code point 范围：U+1F000 ~ U+1FFFF 等（> 0xFFFF）
- 需要 4 字节 UTF-8 编码
- Word 使用 `w:hAnsi` 作为这些字符的 catch-all 字体

### 解决方案

#### 方案一：逐字符检测 + 分割处理（推荐）

```python
import re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def _add_text_with_emoji(self, paragraph, text, bold=False, italic=False, strike=False, code=False):
    """添加文本，将 emoji 分割为独立 run 并设置正确字体"""

    # Emoji Unicode 范围（覆盖主流 emoji）
    emoji_pattern = re.compile(
        '['
        '\U0001F600-\U0001F64F'  # emoticons
        '\U0001F300-\U0001F5FF'  # symbols & pictographs
        '\U0001F680-\U0001F6FF'  # transport & map symbols
        '\U0001F700-\U0001F77F'  # alchemical symbols
        '\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
        '\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
        '\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
        '\U0001FA00-\U0001FA6F'  # Chess Symbols
        '\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
        '\U00002702-\U000027B0'  # Dingbats
        '\U000024C2-\U0000257F'  # Enclosed characters
        '\U00002600-\U000026FF'  # Misc symbols
        '\U00002700-\U000027BF'  # Dingbats
        '\U0000FE00-\U0000FE0F'  # Variation Selectors
        '\U0001F1E0-\U0001F1FF'  # Flags
        ']+'
    )

    last_end = 0
    for match in emoji_pattern.finditer(text):
        # 添加 emoji 前的普通文本
        if match.start() > last_end:
            run = paragraph.add_run(text[last_end:match.start()])
            # 设置普通文本样式...

        # 添加 emoji，设置专用字体
        emoji_text = match.group()
        run = paragraph.add_run(emoji_text)
        # 设置样式...

        # 🔑 关键：通过 XML 设置 emoji 字体
        r = run._element
        rPr = r.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn('w:hAnsi'), 'Segoe UI Emoji')
        rFonts.set(qn('w:ascii'), 'Segoe UI Emoji')

        last_end = match.end()

    # 添加剩余普通文本
    if last_end < len(text):
        run = paragraph.add_run(text[last_end:])
        # 设置普通文本样式...
```

#### 方案二：全局样式设置（简化版）

如果文档中 emoji 较多，可在样式定义中全局设置：

```python
def _set_style_font_for_emoji(self, style):
    """在样式中设置 emoji 字体作为 fallback"""
    style_el = style.element
    rPr = style_el.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    # hAnsi 作为非 ASCII 字符的 catch-all
    rFonts.set(qn('w:hAnsi'), 'Segoe UI Emoji')
```

**注意**：此方案可能影响其他非 ASCII 字符（如带音标的字母）的显示。

### 坑点复盘

| 尝试 | 方法 | 结果 | 原因 |
|------|------|------|------|
| 1 | 更改全局字体为 `Segoe UI Historic` | 方框（无问号） | 字体不支持 emoji |
| 2 | 设置 `w:cs` 属性 | 仍为方框 | `w:cs` 用于复杂脚本，非 emoji |
| 3 | 仅设置 `w:hAnsi` | 部分生效 | 需同时设置 `w:ascii` |
| 4 | 分割 emoji + 设置双属性 | ✅ 成功 | 正确的字体属性组合 |

### Windows 平台 Emoji 字体

| 字体 | 说明 |
|------|------|
| `Segoe UI Emoji` | Windows 内置彩色 emoji 字体（推荐） |
| `Segoe UI Historic` | 历史字符，不支持 emoji |
| `Noto Color Emoji` | Google 开源，需额外安装 |

### 相关记录

- [md-to-word-converter-implementation.md](./md-to-word-converter-implementation.md) - Markdown 转 Word 转换器整体实现

### 参考链接

- [python-docx Font Documentation](https://python-docx.readthedocs.io/en/latest/dev/analysis/features/text/font.html)
- [GitHub Issue #1191 - Font style not applying to unicode text](https://github.com/python-openxml/python-docx/issues/1191)
- [Stack Overflow - python-docx rFonts configuration](https://stackoverflow.com/questions/78829461/python-docx-change-name-of-font-in-wcs-converting-font-encoding-to-unicode)
- [Microsoft Typography - Segoe UI Emoji](https://learn.microsoft.com/en-us/typography/font-list/segoe-ui-emoji)

### 验证记录
- [2026-03-13] 初次记录，基于 md-to-word skill 开发过程中的踩坑总结
- [2026-03-13] 实际测试验证：emoji（😀❤️👍✅🔥等）在 Word 2019+ 正常显示为彩色表情
