# Turns docs/writeup.md into one-page HTML; print it to docs/writeup.pdf with headless Chrome:
#   python docs/build_writeup_pdf.py docs/writeup.md /tmp/w.html 9
#   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=docs/writeup.pdf file:///tmp/w.html
# Needs the `markdown` package. Check it is still one page after any edit.
import sys, re, markdown, pathlib
src, out, size = sys.argv[1], sys.argv[2], sys.argv[3]
md = pathlib.Path(src).read_text()
md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
body = markdown.markdown(md, extensions=["tables"])
css = f"""@page {{ size: Letter; margin: 0.35in 0.45in; }}
body {{ font-family: Helvetica, Arial, sans-serif; font-size: {size}pt; line-height: 1.22; color: #1F2933; }}
h1 {{ font-size: {float(size)+6}pt; margin: 0 0 4pt; color: #0B2A4A; }}
h2 {{ font-size: {float(size)+1.5}pt; margin: 5pt 0 1pt; color: #0B2A4A; }}
p, ul {{ margin: 2pt 0 4pt; }} ul {{ padding-left: 16pt; }} li {{ margin: 1pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0; font-size: {float(size)-0.5}pt; }}
th, td {{ border-bottom: 1px solid #C9D1D9; padding: 2pt 4pt; text-align: left; }} th {{ background: #EEF2F6; }}
a {{ color: #0B2A4A; }}"""
pathlib.Path(out).write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}")
