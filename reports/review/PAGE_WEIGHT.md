# Initial page load before and after review task E7

Measured on the production build (`vite preview`), default view (Nepal, Explore), from the browser's resource timing
after 6 seconds. Encoded = bytes over the wire with the server's compression; decoded = bytes after decompression.

| | Requests | Encoded | Decoded |
|---|---:|---:|---:|
| Before (globe rendered inside the calendar panel) | 13 | 2,692 KB | 14,541 KB |
| After (calendar first; globe loads only on "Open the 3D Earth view") | 9 | 233 KB | 793 KB |

The 3D Earth's code (551 KB) and data (`globe.json` 12.7 MB, world outlines 0.5 MB) now load only when opened.
Country data were already loaded on demand, one country file at a time. No source maps are built or deployed
(`dist/` contains no `.map` files). Rough slow-phone estimate (about 400 kbps): about 5 s for the first load instead
of about 54 s; not measured with throttling.
