"""Fallback deck builder: the same seven-slide layout as generate_slides.mjs, without the Codex-only toolchain.

generate_slides.mjs needs @oai/artifact-tool and a presentation-skill finalizer that exist only in the original Codex
runtime. This script reads the same submission/SLIDES.md, applies the same word limits, and reproduces the same
positions, colours and fonts:
  * an editable PPTX (python-pptx): native text boxes, speaker notes with sources, and the native slide-4 table;
  * 2560x1440 slide renders drawn with Pillow from the same layout, packaged into the PDF by render_slides_pdf.py.
The PDF pages are these Pillow renders, not renders of the PPTX file; both come from the same layout code below.

Usage: python submission/build_deck_fallback.py
Requires python-pptx, Pillow, reportlab and pypdf; Arial from the operating system (Windows: C:/Windows/Fonts).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Pt

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
W, H = 1280, 720
EMU = 12192000 // W  # 9525 EMU per layout pixel (13.333 in x 7.5 in)
SCALE = 2
C = {"bg": "#111b20", "panel": "#18252b", "text": "#f2eee5", "muted": "#aebdc0", "orange": "#f79963", "line": "#42575e", "head": "#283b40"}
FONTS = {False: "C:/Windows/Fonts/arial.ttf", True: "C:/Windows/Fonts/arialbd.ttf"}


def clean(text):
    text = re.sub(r"\*\*|`", "", text)
    return re.sub(r"^[-*] ", "", text, flags=re.M).strip()


def words(text):
    return len(re.findall(r"\S+", clean(text)))


def parse():
    md = (HERE / "SLIDES.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    out = []
    for m in re.finditer(r"^## Slide (\d+) [—-] (.+)\n([\s\S]*?)(?=^## Slide |\Z)", md, re.M):
        sections = {s.group(1): s.group(2).strip() for s in re.finditer(r"^### (.+)\n([\s\S]*?)(?=^### |\Z)", m.group(3), re.M)}
        raw = sections.get("On-slide text", "")
        table_lines = [l for l in raw.split("\n") if l.startswith("|")]
        table = [[clean(c) for c in l.split("|")[1:-1]] for l in table_lines if not re.match(r"^\|[\s:|-]+\|$", l)]
        prose = clean("\n".join(l for l in raw.split("\n") if not l.startswith("|")))
        title, notes, number = clean(m.group(2)), sections.get("Speaker notes", ""), int(m.group(1))
        count = words(" ".join([title, prose] + [c for row in table for c in row])) + (1 if number == 1 else 0)
        if count > 40:
            raise SystemExit(f"Slide {number} has {count} authored words")
        if not 60 <= words(notes) <= 90:
            raise SystemExit(f"Slide {number} has {words(notes)} spoken-note words")
        out.append(dict(number=number, title=title, prose=prose, table=table, notes=notes, sources=sections.get("Sources", ""),
                        visual=sections.get("Visual", ""), authoredWords=count, spokenWords=words(notes)))
    if [s["number"] for s in out] != list(range(1, 8)):
        raise SystemExit("Expected exactly seven sequential slides")
    return md, out


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def layout(item):
    """Return the drawing operations for one slide (same coordinates as generate_slides.mjs)."""
    p = paragraphs(item["prose"])
    rest = lambda k: "\n\n".join(p[k:])
    ops = []
    t = lambda text, x, y, w, h, size=30, color="text", bold=False, link=None: ops.append(("text", clean(text), x, y, w, h, size, C[color], bold, link))
    pic = lambda rel, x, y, w, h, crop=None: ops.append(("image", rel, x, y, w, h, crop))
    n = item["number"]
    if n == 1:
        t("CINDERLINE", 64, 52, 410, 46, 30, "orange", True); t(item["title"], 64, 132, 470, 150, 55, "text", True)
        t(p[0], 64, 322, 440, 95, 34, "orange"); t(rest(1), 64, 442, 440, 150, 29, "muted")
        pic("submission/assets/live-calendar.jpg", 550, 140, 675, 422)
    elif n == 2:
        t(item["title"], 64, 42, 1152, 82, 48, "text", True); t(p[0], 64, 143, 420, 66, 42, "orange", True)
        t(p[1], 700, 143, 516, 66, 42, "orange", True); t(rest(2), 64, 218, 1152, 58, 26, "muted")
        pic("reports/review/aqua_vs_converted_viirs_Nepal.png", 64, 290, 1152, 367)
    elif n == 3:
        t(item["title"], 64, 42, 1152, 110, 48, "text", True); t(p[0], 64, 183, 750, 65, 34, "orange", True)
        t(p[1], 64, 288, 735, 115, 32); t(rest(2).replace(" → ", "\n→ "), 64, 440, 735, 200, 32, "muted")
        pic("submission/assets/live-evidence.jpg", 935, 165, 265, 526, (0.675, 0, 0.01, 0))
    elif n == 4:
        t(item["title"], 64, 42, 1152, 110, 48, "text", True); t(p[0], 64, 169, 1152, 56, 30, "orange")
        ops.append(("table", item["table"], 64, 252, 1152, 268, [330, 210, 320, 292]))
        t(rest(1), 64, 573, 1152, 86, 28, "muted")
    elif n == 5:
        t(item["title"], 64, 42, 1152, 110, 48, "text", True); t(p[0], 64, 190, 695, 98, 32, "muted")
        t(p[1], 64, 345, 695, 120, 40, "orange", True); t(rest(2), 64, 520, 695, 120, 30)
        pic("submission/assets/live-outage.jpg", 914, 165, 286, 526, (0.65, 0, 0.01, 0))
    elif n == 6:
        t(item["title"], 64, 42, 1152, 110, 48, "text", True); t(p[0], 64, 189, 390, 112, 34, "orange", True)
        t(p[1], 64, 340, 390, 170, 28); t(rest(2), 64, 553, 390, 116, 28, "muted")
        pic("submission/assets/live-rhythm-map.jpg", 494, 184, 722, 451)
    else:
        t(item["title"], 64, 45, 1152, 100, 48, "text", True); t(p[0], 64, 192, 790, 110, 38, "orange", True)
        t(p[1], 64, 347, 790, 140, 30)
        for i, line in enumerate(p[2:]):
            t(line, 64, 544 + i * 58, 1152, 50, 28, "orange", False, f"https://{clean(line)}")
        pic("submission/assets/live-calendar.jpg", 920, 192, 296, 185)
    return ops


def contain(img_w, img_h, crop, x, y, w, h):
    l, t_, r, b = crop or (0, 0, 0, 0)
    cw, ch = img_w * (1 - l - r), img_h * (1 - t_ - b)
    s = min(w / cw, h / ch)
    dw, dh = cw * s, ch * s
    return x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, (l, t_, r, b)


def rgb(hex_):
    return RGBColor.from_string(hex_.lstrip("#"))


def build_pptx(slides, path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(W * EMU), Emu(H * EMU)
    blank = prs.slide_layouts[6]
    evidence = []
    for item in slides:
        s = prs.slides.add_slide(blank)
        s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(C["bg"])
        s.notes_slide.notes_text_frame.text = f"{item['notes']}\n\nSOURCES (not spoken)\n{item['sources']}\n\nVISUAL PROVENANCE (not spoken)\n{item['visual']}"
        for op in layout(item):
            if op[0] == "text":
                _, text, x, y, w, h, size, color, bold, link = op
                box = s.shapes.add_textbox(Emu(x * EMU), Emu(y * EMU), Emu(w * EMU), Emu(h * EMU))
                tf = box.text_frame; tf.word_wrap = True
                for attr in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
                    setattr(tf, attr, 0)
                for i, para in enumerate(text.split("\n")):
                    par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    run = par.add_run(); run.text = para
                    run.font.name, run.font.size, run.font.bold = "Arial", Pt(size * 0.75), bold
                    run.font.color.rgb = rgb(color)
                    if link:
                        run.hyperlink.address = link
            elif op[0] == "image":
                _, rel, x, y, w, h, crop = op
                src = REPO / rel
                with Image.open(src) as im:
                    iw, ih = im.size
                dx, dy, dw, dh, (l, t_, r, b) = contain(iw, ih, crop, x, y, w, h)
                shape = s.shapes.add_picture(str(src), Emu(int(dx * EMU)), Emu(int(dy * EMU)), Emu(int(dw * EMU)), Emu(int(dh * EMU)))
                shape.crop_left, shape.crop_top, shape.crop_right, shape.crop_bottom = l, t_, r, b
                shape.name = f"Original evidence: {rel}"
                evidence.append({"slide": item["number"], "path": rel, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "crop": crop and dict(zip(("left", "top", "right", "bottom"), crop))})
            else:
                _, rows, x, y, w, h, colw = op
                tbl = s.shapes.add_table(len(rows), len(rows[0]), Emu(x * EMU), Emu(y * EMU), Emu(w * EMU), Emu(h * EMU)).table
                for j, cw in enumerate(colw):
                    tbl.columns[j].width = Emu(cw * EMU)
                for i, row in enumerate(rows):
                    for j, value in enumerate(row):
                        cell = tbl.cell(i, j); cell.fill.solid(); cell.fill.fore_color.rgb = rgb(C["head"] if i == 0 else C["panel"])
                        cell.text = value
                        run = cell.text_frame.paragraphs[0].runs[0]
                        run.font.name, run.font.size, run.font.bold = "Arial", Pt((26 if i == 0 else 30) * 0.75), i == 0
                        run.font.color.rgb = rgb(C["orange"] if i == 0 else C["text"])
    prs.save(path)
    return evidence


def wrap(draw, text, font, width):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append(""); continue
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}".strip()
            if draw.textlength(trial, font=font) <= width or not line:
                line = trial
            else:
                lines.append(line); line = word
        lines.append(line)
    return lines


def render_png(item, path):
    img = Image.new("RGB", (W * SCALE, H * SCALE), C["bg"])
    d = ImageDraw.Draw(img)
    for op in layout(item):
        if op[0] == "text":
            _, text, x, y, w, h, size, color, bold, _ = op
            font = ImageFont.truetype(FONTS[bold], size * SCALE)
            line_h = size * SCALE * 1.18
            for k, line in enumerate(wrap(d, text, font, w * SCALE)):
                d.text((x * SCALE, y * SCALE + k * line_h), line, font=font, fill=color)
        elif op[0] == "image":
            _, rel, x, y, w, h, crop = op
            with Image.open(REPO / rel) as im:
                im = im.convert("RGB"); iw, ih = im.size
                dx, dy, dw, dh, (l, t_, r, b) = contain(iw, ih, crop, x, y, w, h)
                im = im.crop((int(iw * l), int(ih * t_), int(iw * (1 - r)), int(ih * (1 - b)))).resize((int(dw * SCALE), int(dh * SCALE)), Image.LANCZOS)
                img.paste(im, (int(dx * SCALE), int(dy * SCALE)))
        else:
            _, rows, x, y, w, h, colw = op
            row_h = h / len(rows)
            for i, row in enumerate(rows):
                cx = x
                for j, value in enumerate(row):
                    box = [cx * SCALE, (y + i * row_h) * SCALE, (cx + colw[j]) * SCALE, (y + (i + 1) * row_h) * SCALE]
                    d.rectangle(box, fill=C["head"] if i == 0 else C["panel"], outline=C["line"], width=SCALE)
                    font = ImageFont.truetype(FONTS[i == 0], (26 if i == 0 else 30) * SCALE)
                    th = font.getbbox("Ag")[3]
                    d.text((box[0] + 18 * SCALE, box[1] + (box[3] - box[1] - th) / 2), value, font=font, fill=C["orange"] if i == 0 else C["text"])
                    cx += colw[j]
    img.save(path)


def main():
    md, slides = parse()
    build = REPO / ".deck-build" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    rendered = build / "rendered"; rendered.mkdir(parents=True, exist_ok=True)
    pptx = build / "FIRETRACE_slides.pptx"
    evidence = build_pptx(slides, pptx)
    for item in slides:
        render_png(item, rendered / f"slide-{item['number']}.png")
    manifest = {"createdUtc": datetime.now(timezone.utc).isoformat(), "source": "submission/SLIDES.md",
                "sourceSha256": hashlib.sha256(md.encode("utf-8")).hexdigest(), "sourceHashNormalization": "LF", "slideCount": 7,
                "slides": [{k: s[k] for k in ("number", "title", "authoredWords", "spokenWords")} for s in slides],
                "wordCountScope": "Authored title and slide copy, including native table cells and cover brand. Unmodified source screenshot/figure labels are retained as evidence and excluded from this prose limit.",
                "evidence": evidence,
                "generator": "submission/build_deck_fallback.py (python-pptx + Pillow), same layout as generate_slides.mjs; the Codex artifact-tool runtime was not available.",
                "editability": {"pptx": "Native editable text, speaker notes with sources, and the slide-4 results table. Screenshots and figures remain embedded images.",
                                "pdf": "Raster pages drawn by Pillow from the same layout (not renders of the PPTX): text is not selectable and this is not a tagged accessible PDF. Use SLIDES.md or the PPTX for text."},
                "rendered": str(rendered)}
    (build / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    pdf = build / "FIRETRACE_slides.pdf"
    subprocess.run([sys.executable, str(HERE / "render_slides_pdf.py"), str(build / "manifest.json"), str(pdf)], check=True, cwd=REPO)
    for src, name in ((pptx, "FIRETRACE_slides.pptx"), (pdf, "FIRETRACE_slides.pdf")):
        (HERE / name).write_bytes(src.read_bytes())
    manifest["outputs"] = [{"path": f"submission/FIRETRACE_slides.{fmt}", "sha256": hashlib.sha256((HERE / f"FIRETRACE_slides.{fmt}").read_bytes()).hexdigest(),
                            "bytes": (HERE / f"FIRETRACE_slides.{fmt}").stat().st_size} for fmt in ("pptx", "pdf")]
    public = {k: v for k, v in manifest.items() if k != "rendered"}
    (HERE / "assets/deck-manifest.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"build": str(build), "outputs": manifest["outputs"]}, indent=1))


if __name__ == "__main__":
    main()
