"""Build a clean HTML report from the notebook for printing to PDF.

Usage: py -3 build_report.py
Opens: report.html (open in browser, then Print -> Save as PDF)
"""
import json, base64, html, os, re, sys

NB = 'Project_2.ipynb'
OUT = 'report.html'

# Cells to skip entirely (e.g. data loading or pure technical cells if needed)
SKIP_CELLS = set()

# Code cells whose CODE we hide but whose OUTPUT we keep (e.g. print setup if any)
HIDE_CODE_KEEP_OUTPUT = set()

with open(NB, 'r', encoding='utf-8') as f:
    nb = json.load(f)


def encode_image(mime: str, b64: str) -> str:
    return f'<img class="cell-image" src="data:{mime};base64,{b64}" />'


def render_markdown(src: str) -> str:
    """Convert minimal Markdown to HTML. Preserves <div dir="rtl"> blocks as-is."""
    out = src

    # Headings (preserve LaTeX inside)
    out = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', out, flags=re.M)
    out = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', out, flags=re.M)
    out = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', out, flags=re.M)
    out = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', out, flags=re.M)

    # Tables: detect blocks of lines that contain |
    lines = out.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith('|') and '|' in ln.strip()[1:]:
            # collect table block
            tbl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl.append(lines[i])
                i += 1
            new_lines.append(_render_table(tbl))
            continue
        new_lines.append(ln)
        i += 1
    out = '\n'.join(new_lines)

    # Lists
    out = re.sub(r'(^- .+(\n  .+)*)+', _render_list, out, flags=re.M)

    # Inline: bold, italic, code
    out = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', out)
    out = re.sub(r'`([^`]+)`', r'<code>\1</code>', out)

    paragraphs = re.split(r'\n{2,}', out)
    final = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if re.match(r'^<(h\d|div|table|ul|ol|pre|hr)', p):
            final.append(p)
        else:
            p = p.replace('\n', '<br>\n')
            final.append(f'<p>{p}</p>')
    return '\n\n'.join(final)


def _render_table(lines):
    rows = []
    for ln in lines:
        ln = ln.strip().strip('|')
        cells = [c.strip() for c in ln.split('|')]
        rows.append(cells)
    if len(rows) >= 2 and all(re.match(r'^:?-+:?$', c) for c in rows[1]):
        header = rows[0]
        body = rows[2:]
    else:
        header = None
        body = rows
    out = ['<table>']
    if header:
        out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in header) + '</tr></thead>')
    out.append('<tbody>')
    for r in body:
        out.append('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def _render_list(m):
    block = m.group(0)
    items = re.split(r'\n(?=- )', block)
    out = ['<ul>']
    for it in items:
        it = re.sub(r'^- ', '', it).strip()
        out.append(f'  <li>{it}</li>')
    out.append('</ul>')
    return '\n'.join(out)


def render_code_output(out):
    pieces = []
    ot = out.get('output_type')
    if ot == 'stream':
        text = ''.join(out.get('text', []))
        pieces.append(f'<pre class="output">{html.escape(text)}</pre>')
    elif ot in ('display_data', 'execute_result'):
        data = out.get('data', {})
        if 'image/png' in data:
            b64 = data['image/png']
            if isinstance(b64, list):
                b64 = ''.join(b64)
            pieces.append(encode_image('image/png', b64))
        elif 'text/plain' in data:
            text = ''.join(data['text/plain']) if isinstance(data['text/plain'], list) else data['text/plain']
            pieces.append(f'<pre class="output">{html.escape(text)}</pre>')
    elif ot == 'error':
        text = '\n'.join(out.get('traceback', []))
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        pieces.append(f'<pre class="error">{html.escape(text)}</pre>')
    return '\n'.join(pieces)


body_parts = []

for i, cell in enumerate(nb['cells']):
    if i in SKIP_CELLS:
        continue
    ct = cell['cell_type']
    src = ''.join(cell['source'])
    if ct == 'markdown':
        body_parts.append('<section class="md">')
        body_parts.append(render_markdown(src))
        body_parts.append('</section>')
    elif ct == 'code':
        body_parts.append('<section class="code-cell">')
        if i not in HIDE_CODE_KEEP_OUTPUT:
            body_parts.append(f'<pre class="code">{html.escape(src)}</pre>')
        for out in cell.get('outputs', []):
            body_parts.append(render_code_output(out))
        body_parts.append('</section>')

CSS = """
@page { size: A4; margin: 18mm 16mm; }
html, body { direction: rtl; }
body {
  font-family: 'Segoe UI', 'David', 'Times New Roman', serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #1a1a1a;
  max-width: 880px;
  margin: 0 auto;
  padding: 18px 24px;
  background: #fff;
}
h1, h2, h3, h4 {
  color: #0b3a66;
  margin-top: 1.3em;
  margin-bottom: 0.4em;
  page-break-after: avoid;
}
h1 { font-size: 22pt; border-bottom: 2px solid #0b3a66; padding-bottom: 4px; }
h2 { font-size: 16pt; border-bottom: 1px solid #cdd9e6; padding-bottom: 3px; }
h3 { font-size: 13pt; }
h4 { font-size: 11.5pt; color: #2c5d8f; }
p { margin: 0.5em 0; }
ul { margin: 0.5em 1.5em; }
li { margin: 0.25em 0; }
strong { color: #0b3a66; }
code {
  background: #f4f6f8;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'Consolas', 'Cascadia Code', monospace;
  font-size: 10pt;
  direction: ltr;
  display: inline-block;
}
pre.code {
  direction: ltr;
  text-align: left;
  background: #f8f9fb;
  border: 1px solid #e4e8ee;
  border-right: 4px solid #6c8cb0;
  padding: 10px 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Cascadia Code', monospace;
  font-size: 9.5pt;
  line-height: 1.4;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  page-break-inside: avoid;
}
pre.output {
  direction: ltr;
  text-align: left;
  background: #fbfbf6;
  border-right: 4px solid #c7b96e;
  padding: 8px 12px;
  font-family: 'Consolas', 'Cascadia Code', monospace;
  font-size: 9.5pt;
  line-height: 1.35;
  margin: 4px 0 10px;
  white-space: pre-wrap;
  word-break: break-word;
  page-break-inside: avoid;
  border-radius: 3px;
}
pre.error {
  direction: ltr;
  text-align: left;
  background: #fff0f0;
  border-right: 4px solid #c0392b;
  padding: 8px 12px;
  font-family: 'Consolas', monospace;
  font-size: 9.5pt;
}
table {
  border-collapse: collapse;
  margin: 0.8em auto;
  font-size: 10.5pt;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #cdd6e0;
  padding: 5px 10px;
  text-align: center;
}
th { background: #eef3f8; color: #0b3a66; font-weight: 600; }
tbody tr:nth-child(even) { background: #fafbfd; }
img.cell-image {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 10px auto;
  border: 1px solid #e0e4ea;
  border-radius: 3px;
  page-break-inside: avoid;
}
section.md, section.code-cell { page-break-inside: auto; }
section.code-cell { margin-bottom: 12px; }
section.md { margin-bottom: 8px; }
.title-block {
  text-align: center;
  border-bottom: 3px double #0b3a66;
  padding-bottom: 12px;
  margin-bottom: 20px;
}
.title-block h1 { border: none; margin: 0; font-size: 26pt; }
.title-block .subtitle { font-size: 13pt; color: #555; margin-top: 6px; }
.title-block .meta { font-size: 10.5pt; color: #777; margin-top: 4px; }
@media print {
  body { padding: 0; max-width: none; }
  pre.code, pre.output, table, img.cell-image { page-break-inside: avoid; }
}
"""

HEAD = f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8" />
<title>Project 2 — Spectral Analysis</title>
<style>{CSS}</style>
<script>
  MathJax = {{
    tex: {{ inlineMath: [['$','$']], displayMath: [['$$','$$']] }},
    svg: {{ fontCache: 'global' }}
  }};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<div class="title-block">
  <h1>פרויקט 2 — עיבוד אותות במוח</h1>
  <div class="subtitle">Spectral Analysis, Welch PSD, and Time-Frequency Representations</div>
  <div class="meta">Roy Carmelli · אוניברסיטת בר-אילן · מאי 2026<br>
  <a href="https://github.com/Royc4515/Project2_SignalProcessing" style="color: #0b3a66; text-decoration: none; font-weight: bold;">🔗 צפייה במאגר הפרויקט ב-GitHub</a></div>
</div>
"""

FOOT = "\n</body>\n</html>\n"

html_out = HEAD + '\n'.join(body_parts) + FOOT
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html_out)

size_kb = os.path.getsize(OUT) / 1024
print(f"Wrote {OUT} ({size_kb:.1f} KB)")
print("Open in browser, then Ctrl+P -> Save as PDF.")
