"""Package verified PPTX slide renders as a seven-page PDF; no scientific edits.

Usage: python submission/render_slides_pdf.py MANIFEST_JSON OUTPUT_PDF
Requires ReportLab, Pillow and pypdf. PPTX remains the editable deliverable.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image
from pypdf import PdfReader
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def main() -> None:
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    destination = Path(sys.argv[2])
    destination.parent.mkdir(parents=True, exist_ok=True)
    width, height = 960, 540  # 16:9, matching the 1280x720 native slide canvas.
    pdf = canvas.Canvas(str(destination), pagesize=(width, height), pageCompression=1)
    pdf.setTitle("FIRETRACE — Seven-slide judging deck")
    pdf.setAuthor("FIRETRACE team")
    pdf.setSubject("Historical fire observations, frozen calibration and visible limitations")
    for slide in manifest["slides"]:
        picture = Path(manifest["rendered"]) / f"slide-{slide['number']}.png"
        with Image.open(picture) as image:
            if image.width * 9 != image.height * 16:
                raise ValueError(f"Unexpected slide aspect ratio: {picture}")
        pdf.bookmarkPage(f"slide-{slide['number']}")
        pdf.addOutlineEntry(slide["title"], f"slide-{slide['number']}", level=0)
        pdf.drawImage(ImageReader(str(picture)), 0, 0, width=width, height=height)
        if slide["number"] == 7:
            pdf.linkURL("https://github.com/Water-Mal0ne/FIRETRACE", (48, 91, 912, 132), relative=0)
            pdf.linkURL("https://firetrace-bhaktapur-2026.pages.dev/", (48, 47, 912, 88), relative=0)
        pdf.showPage()
    pdf.save()
    if len(PdfReader(str(destination)).pages) != 7:
        raise ValueError("Expected exactly seven PDF pages")
    print(f"Seven-page PDF verified: {destination}")


if __name__ == "__main__":
    main()
