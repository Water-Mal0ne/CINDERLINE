# CINDERLINE slide artifact checks

Rebuilt 2026-11-15 09:19 UTC for the CINDERLINE rename and the Kathmandu, Nepal local event. The PDF and PowerPoint each contain exactly seven slides, matching `submission/SLIDES.md`.

- **Generator:** `submission/build_deck_fallback.py`. The original `generate_slides.mjs` needs `@oai/artifact-tool` and a presentation-skill finalizer that exist only in the Codex runtime, so they could not be run here. The fallback reads the same `SLIDES.md`, applies the same word limits, and reproduces the same positions, colours and Arial font. It uses python-pptx for the PPTX and Pillow renders for the PDF, which `submission/render_slides_pdf.py` packages.
- **Word counts:** authored words per slide, including titles, table cells and the cover brand: **22, 20, 27, 38, 32, 28, 22** (limit 40). Spoken speaker-note words: **70, 72, 74, 81, 75, 82, 81** (60-90). Source and visual-provenance references follow the spoken notes under separate, unspoken labels.
- **Editable content:** titles, body text, speaker notes and the slide-4 results table are native and editable in the PPTX. Screenshots and the Nepal comparison chart are embedded unchanged as images; the evidence-card crops keep their caveat text.
- **Screenshots:** the five application screenshots are the original captures (`CAPTURE_PROVENANCE.json`). None of the cropped views shows the old product name.
- **Checked:** all seven Pillow renders were inspected, and the PDF page count, title, author and links were checked. Its links go to the repository and https://cinderline-spaceapps.pages.dev/.
- **PDF limits:** the PDF contains raster pages drawn by Pillow from the same layout, not renders of the PPTX file. Its text is not selectable and it is not a tagged accessible PDF. Use `submission/SLIDES.md` or the PPTX for text.
- **Not done:** PowerPoint desktop save/reopen and the original Artifact Tool package and layout validators were not run.

`submission/assets/deck-manifest.json` records the LF-normalized Markdown hash, image and output hashes, word counts, generator and editability limits.

Final artifacts (file names kept unchanged):

- `submission/FIRETRACE_slides.pptx`: 508,924 bytes; SHA-256 `d67820a76a15fc742d4bc1a7d13784608a42e1ba514e61730af2da04f4a5ee7c`.
- `submission/FIRETRACE_slides.pdf`: 3,688,302 bytes; SHA-256 `6106a986c9fe082e5b895c0184e0e7c713f96bfa2615d3d03627b7bf9a5c6ccd`.

Rebuild with `python submission/build_deck_fallback.py`, or with `node submission/generate_slides.mjs --modules … --skill … --python …` where the Codex runtime is available.
