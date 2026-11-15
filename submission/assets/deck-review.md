# FIRETRACE slide artifact checks

Reviewed 2026-11-14 20:16 UTC. The PDF and PowerPoint each contain exactly seven slides, matching `submission/SLIDES.md`.

- All seven final PowerPoint slide renders were inspected; all seven PDF pages were rendered with Poppler and inspected. The final metadata-only rebuild is pixel-identical to the independently approved slide renders.
- Native authored word counts, including titles, table cells and the cover brand: **18, 20, 27, 34, 28, 28, 22**. Original screenshot and scientific-figure labels remain intact as source evidence and are excluded from this authored-prose limit.
- Spoken speaker-note counts: **70, 72, 74, 80, 78, 82, 81**. Documentary source and visual-provenance references follow the spoken text under separate, unspoken labels.
- Package integrity, slide geometry, font policy and Artifact Tool re-import checks pass. The installed design font is Arial. The held-out results table on slide 4 is a native editable table.
- Existing source screenshots and the Nepal comparison chart are embedded without changing their observations. Evidence-card crops retain the visible caveat text. The map is explicitly described as exploratory, and the season finding as retrospective.
- Titles, body text, the results table and speaker notes remain editable in the PPTX. Embedded source screenshots and figures remain images.
- **The PDF contains raster slide pages, so its text is not selectable and it is not a tagged accessible PDF.** Use `submission/SLIDES.md` for selectable text and complete notes, or the editable PowerPoint. The PDF uses verified high-resolution renders because the bundled native PDF exporter could not resolve `#standard-fonts/Helvetica`.
- PowerPoint desktop save/reopen was not performed. Structural checks and renderer checks do not replace testing in that application.

`submission/assets/deck-manifest.json` records the LF-normalized Markdown hash, exact image and output hashes, runtime versions, word counts, editability limits and reproduction command. It contains no personal filesystem paths. The scientific evidence and source commits are recorded separately in `submission/evidence/SOURCE_LEDGER.md`.

Final artifacts:

- `submission/FIRETRACE_slides.pptx`: 576,251 bytes; SHA-256 `55cfdf62a1e1904df94772af8af52ee1aa635e7b797322a964c32442df313a1e`.
- `submission/FIRETRACE_slides.pdf`: 3,356,638 bytes; SHA-256 `2db65365ff2de1eea4615f7fab2fc73069919560a644d3da239a6c4f8d7371d0`.

Rebuild with `submission/generate_slides.mjs` and its documented runtime arguments. `submission/render_slides_pdf.py` packages the verified final-PPTX renders. Private build and validation intermediates are intentionally outside the submitted artifact set.
