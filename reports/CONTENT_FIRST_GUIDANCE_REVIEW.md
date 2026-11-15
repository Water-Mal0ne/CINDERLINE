# Chrome Modern Web Guidance review

Independent source review of `test/content-first-redesign`, based on `7d390c4`.
Reviewed on 2026-11-15. This report is a source audit, not a claim of complete accessibility conformance or measured Core Web Vitals.

## Primary references and implementation

| Chrome guide | Application in this experiment | Verification |
| --- | --- | --- |
| [Maximize content and reduce noise](https://developer.chrome.com/docs/modern-web-guidance/guides/user-experience/content-first-noise-reduction) | Compact header; Calendar, Patterns and Earth have separate workspaces; Weekly and Monthly are alternatives; area/date controls and secondary scientific detail use native disclosures. | Source checked. No promotional overlay or auto-opening interruption added. Filters expand in document flow. |
| [Adapt to the form factor](https://developer.chrome.com/docs/modern-web-guidance/guides/user-experience/form-factor-adaptation) | Named container queries adapt monthly comparison, rhythm charts and Earth controls. Controls wrap; touch targets are enlarged; headings use balanced wrapping. | Source checked; 320px reflow, native select labels and dense calendar targets require browser verification. |
| [Tabbed interfaces](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/tabs) | Top-level page navigation retains navigation semantics. Workspace selectors are explicitly labeled button groups with pressed states, rather than partial ARIA tablists. The selected workspace has an underline. | Source checked. Keyboard activation and visible selection in forced colors require browser verification. |
| [Accessibility coding guidelines](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/accessibility) | Skip link, named landmarks, actual buttons/selects, labeled chart summaries, table headers, visible focus, error recovery, and reduced-motion support retained. | Source checked. Dialog isolation, focus return and a full keyboard walkthrough are required before preview acceptance. |
| [CSS layouts and responsive design](https://developer.chrome.com/docs/modern-web-guidance/guides/css/css-layout) | Grid is used for columns, flex for toolbars, flexible tracks and minimum-width resets for charts. Scientific data tables retain internal horizontal scrolling instead of dropping columns. | Source checked. Browser check must distinguish allowed chart/table scrolling from page overflow. |
| [Performance](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/performance) | Earth and seasonal comparison remain lazy modules. Earth is mounted on demand. Spatial rhythm data are requested only after that view is opened; FRP mounts only after its disclosure opens. | Source checked. No new framework or visual library dependency. Network ordering and runtime errors need browser confirmation. |
| [Typography](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/typography) and [OS text scale](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/respect-os-text-scale) | Relative font sizes and a browser-controlled root size are required for text settings to work. | Initial audit identified remaining fixed-pixel text; correction is tracked below. Test 200% text and 320px reflow after correction. |

## Findings raised during implementation

1. **Coarse-pointer calendar cascade.** The foundation stylesheet enlarged the weekly calendar to 1400px, but the later workspace stylesheet reset the same selector to 700px with `!important`. That conflicted with the new minimum cell width and could make adjacent hit regions overlap. The parent reported a higher-specificity 1500px correction. Verify the resulting cell rectangles on a touch/coarse-pointer viewport.
2. **Selected state in forced colors.** Segmented controls used background and text color alone. The parent reported a selected-state border pseudo-element correction. Verify Weekly/Monthly, reference scale and pattern selections remain visually distinct with forced colors enabled.
3. **Font request chain.** Existing `styles.css` loaded Google Fonts with CSS `@import`, which the performance guide discourages. The parent reported moving the same request into HTML stylesheet and preconnect links. Confirm there is no CSS font import left in the built output.
4. **Modal background access.** The inherited evidence drawer used a custom `aria-modal` overlay and a manually implemented Tab trap without making background content inert. The workspace agent is replacing it with a native modal dialog. Confirm `showModal()`, Escape, close button, light dismiss and focus return; remove duplicate manual Tab trapping.
5. **Text scaling.** Initial new styles used pixel font sizes while `unslop.css` fixed the root at 14px. The parent is converting preview font declarations to relative units and removing that root override. The Chrome text-scale guide explicitly disallows an author-set root font size, including percentages, when opting in to OS scaling.
6. **Narrow country control.** At 320px, a fixed right padding reserved space for the Area & dates trigger, potentially leaving too little room for United States and its two icons. This is a browser-verification item; prefer content-driven stacking if the name clips.

These findings describe the reviewed intermediate state. The release reviewer should update their status from the final code and browser evidence; a reported fix is not by itself a verified result.

## Preserved boundaries

- `git diff --name-only -- web/public data scripts firetrace tests` was empty at the time of this source audit. Published scientific payloads and Python analysis were unchanged.
- Charts retain existing series, values and uncertainty marks; the presentation changes do not create finer harmonization or new scientific claims.
- Existing charcoal and ember theme remains. Scientific chart palettes remain distinct from navigation styling.
- Only a temporary preview is authorized. This branch must not be merged or deployed to the production Pages project as part of this experiment.

## Browser acceptance checks

- Desktop and 320/390px: country selection, valid and invalid dates, Weekly/Monthly, Patterns and Earth; page itself does not overflow.
- Keyboard: skip link, menu, disclosures, selectors, week navigation, evidence dialog and return to its trigger.
- Evidence-to-Earth and Earth-to-calendar keep the selected country/year/cell; linked `?view=rhythm` still restores rhythm.
- Seven countries; area drawing and radius input; 2025 availability caveat; raw/harmonized distinction; native 2024 observations and point evidence.
- 200% text, reduced motion and forced colors; no overlapping controls or lost information.
- Console and failed requests checked. Do not report physical-device or screen-reader testing unless it was actually performed.


## Final integration status

The six findings above were corrected in this experiment. These are the final evidence boundaries:

- The coarse-pointer rule now has greater specificity than the 700px fallback and supplies a 1500px calendar surface. This was source-checked; a physical touchscreen/coarse-pointer session was not available.
- Pressed segmented controls now have a border underline, and forced-colors focus rules use system colors. Source verified; forced-colors emulation was not available in this browser tool.
- Font loading moved to HTML stylesheet/preconnect links. The CSS font import is removed.
- Evidence is now a native `dialog` opened through `showModal()`, with browser-managed background inertness. Live browser checks confirmed modal state, focus on Close evidence, Escape closure and return to the triggering button. The StrictMode queued-close race found during testing was corrected.
- The browser-controlled root font size is restored; new preview font declarations use rem. Native 200% text preference testing was not performed. A 320px viewport reflow check is not represented as a text-preference test.
- The country select uses the full mobile row. United States is fully readable at 320px. Page width was 305px inside the 320px viewport (the remaining space is the scrollbar), with no page overflow.

Full validation: 112 Python tests and 178 web tests passed; TypeScript and production build passed. The build contains 9,003 files, 310,790,886 bytes total; largest file 12,999,487 bytes (below 25 MiB). The existing lazy Earth bundle remains above Vite's 500 kB advisory threshold; it is only loaded when requested.

Browser checks covered all seven country calendars, weekly/monthly switching and monthly-link reload, native week evidence, country results, FRP disclosure, spatial rhythm map, direct `?view=rhythm`, point/radius area calendar, annual Earth, native observation zoom and observation evidence. Phone Earth rendered a 341-by-400 CSS-pixel canvas at 390px viewport with no page overflow. No console errors were captured. This is not a complete screen-reader, physical-device, or Core Web Vitals audit.

Publication is restricted to the separate Cloudflare `cinderline-ui-preview` project and its `content-first` preview branch. Production remains unchanged.
