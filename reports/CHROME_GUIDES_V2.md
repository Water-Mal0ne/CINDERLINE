# Chrome guide applicability and verification — redesign v2

Reviewed 2026-11-15. Source baseline: `955332d`; v2 implementation is isolated on `test/atlas-redesign`. The final source review was performed against the working tree before its release commit. This is an applicability/source audit, not a certification that the site complies with every guideline.

## What “follow every guide” means here

The [Chrome guide catalogue](https://developer.chrome.com/docs/modern-web-guidance/guides) contains **208 entries** on the review date. It mixes foundational requirements, optional UI recipes, experimental APIs and unrelated product features. Every entry is accounted for below. Adding payments, carousels, AI tools or origin-trial APIs to a fire-data application would conflict with the user's request to reduce clutter. The baseline/reference guides and relevant recipes guide this redesign; omitted recipes are explained rather than silently described as passed.

The audit downloaded 75 relevant or related guide bodies for targeted source review; all 208 catalogue entries were inventoried. Source excerpts were inspected for native controls, typography, CSS layout, interaction, accessibility, performance, security and privacy. Downloading a guide is not itself a conformance test.

## Priority findings and acceptance criteria

| Priority | Finding at the first preview | Required correction / evidence |
| --- | --- | --- |
| P1 | Multiple stacked headings, subtitles, metadata rows and panel titles delayed the actual calendar. | One clear page heading/context, chart as the dominant surface, related actions beside content. Remove repetition rather than shrink text. |
| P1 | Numerous accumulated override stylesheets made the same controls vary across pages. | Reconcile shell/layout rules into deliberate layers/tokens. Measure rendered controls across Calendar, Patterns, Earth, Rhythm, Evidence and Methods. |
| P1 | Many inherited font sizes remain fixed px; first preview lacked OS text-scale opt-in. | Use relative font sizes, browser-controlled root, text-scale opt-in, flexible heights; verify at 200% text and 320px reflow. |
| P1 | Weekly targets were 20px high; coarse-pointer targets were 28px. | Meet the guide's 24px base / 44px touch recommendation or supply an equivalent usable control. Do not overlap hit areas. |
| P1 | Essential controls sometimes used faint decorative borders; contrast not measured. | Verify 4.5:1 normal text and 3:1 important control boundaries/states. Selection requires a shape/text cue, not color alone. |
| P1 | `html:has(dialog:modal) {overflow:hidden}` conflicts with the native dialog recipe. | Use dialog/backdrop overscroll containment, avoiding document-root scroll locking and consequent layout shifts. |
| P1 | Repetition removal can accidentally detach caveats from scientific results. | Preserve all scientific quantities and distinct caveats; remove exact duplicates or move repeated mechanics into labeled details. Check raw/harmonized, 2025, outages and observation-layer differences. |
| P2 | Dynamic Google Fonts CSS remains an external request with no fixed SRI. | Prefer self-hosted licensed assets or retain as an explicit known dependency. Never attach an arbitrary stable hash to changing CSS. |
| P2 | No repository HTTP security-header policy found. | Inspect actual preview headers and introduce only tested appropriate protections; do not turn on experimental policies or telemetry just to satisfy a recipe. |
| P2 | Initial HTML root was empty if JavaScript failed/unavailable. | A meaningful noscript fallback and clear runtime recovery should explain how to access the data. |
| P2 | Lazy/unmounted research views are not searchable until opened. | Keep static explanations in native details; direct view URLs and explicit navigation remain available. Document the lazy data-view tradeoff. |

## Baseline source evidence

- Native evidence `dialog.showModal()` already provides focus containment and background inertness; `closedby` has a guarded pointer fallback. Runtime close/focus tests remain necessary after layout changes.
- Week/month controls already have keyboard grid navigation and complete numeric accessible labels. Their physical target sizes still require checking.
- The observation globe has labeled DOM controls and an accessible table alternative. Experimental HTML-in-canvas is unnecessary.
- Both globe implementations use ResizeObserver, IntersectionObserver, hidden-tab handling and demand rendering with disposal. This is positive source evidence, not a measured performance result.
- Country/date/area controls use native form elements and errors; the current country has a valid default, so the required-empty-select recipe is inapplicable.
- Sharing uses Async Clipboard, status announcement and a selectable-link fallback. Its transient panel and failure state need narrow-screen testing.
- No unsafe `innerHTML`, `dangerouslySetInnerHTML`, eval or personal-data localStorage sink was found in the audited source search. That does not replace a security audit of dependencies.
- Published numerical payloads and scientific computation must remain unchanged by this visual redesign.

## Runtime verification matrix

This section is a handoff checklist until final evidence is appended. A source pattern or test-suite result alone is not sufficient to mark a browser behavior passed.

| Area | Required checks |
| --- | --- |
| Every view | Desktop, 390px and 320px; no page-level horizontal overflow, clipped heading, overlapped control or missing action. Chart/table internal overflow may be essential. |
| Text preferences | Browser default-size increase / 200% text, 400% zoom-equivalent reflow, text-spacing overrides; no loss of labels, controls or data. |
| Keyboard | Skip navigation, all main destinations, selectors, disclosures, week/month arrow navigation, evidence close/return focus, exports and table scrolling. |
| High contrast | Forced-colors navigation/selection/focus and missing-data distinctions; essential data accessible through values/table. |
| Motion | Reduced-motion preference; no unexpected automatic movement; globe interaction remains usable. |
| Calendar | Seven countries; weekly/monthly, raw/harmonized, valid/invalid dates, 2025 caveat, no-observation weeks, selected-area scope. |
| Research | Weekly Rhythm Index direct URL, chart/table/spatial views, FRP, held-out results and readable caveats. |
| Earth | Lazy loading, harmonized overview, observed 2024 layer, zoom detail, point evidence, touch-equivalent controls, WebGL fallback. |
| Sharing | Reload same view/context; clipboard denied fallback; no stale share link during country loads. |
| Performance | Cold/warm load, network request order, layout shifts, slow interaction sample and errors; field Core Web Vitals cannot be claimed from a local run. |
| Deployment | Preview project only, no production change; correct commit/assets, HTTP headers and no console errors. |

## Complete catalogue inventory

Codes: **A** = applies to existing behavior and must be reviewed; **O** = optional recipe/conditional enhancement, not an obligation to add a feature; **N** = absent feature/outside scope; **E** = experimental or staged-policy recipe not adopted; **S** = explicit user-scope exception. A is **not** a passed status.

Counts: **A: 66**, **O: 88**, **N: 47**, **E: 6**, **S: 1**.

### Visual Design
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [adapt scrollbar to contrast preferences](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/adapt-scrollbar-to-contrast-preferences) | A | Keep scrollbars visible and legible in high contrast; do not hide navigation affordances. |
| [apply webgl shaders](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/apply-webgl-shaders) | E | HTML-in-canvas shader recipe requires Origin Trial opt-in; stable Three.js scene remains. |
| [color](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/color) | A | Measure text/control contrast; supply non-color selection and system-color fallbacks. |
| [complex shapes](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/complex-shapes) | O | No decorative clipping needed; must not clip data or focus if added. |
| [custom text decorations](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/custom-text-decorations) | O | Simple selection underline suffices; decorative text animation is unnecessary. |
| [customize scrollbar color and thickness](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/customize-scrollbar-color-and-thickness) | O | Native scrollbar styling is sufficient when contrast is preserved. |
| [dark mode](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/dark-mode) | S | User requested existing dark palette; native dark controls remain. Automatic light theme is not implemented. |
| [interactive content in 3d scenes](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/interactive-content-in-3d-scenes) | E | Interactive HTML-in-canvas is experimental; retain DOM controls outside the globe. |
| [contrast color](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/contrast-color) | A | Audit contrast where values determine backgrounds; heatmaps must expose values without color dependence. |
| [equal width text lines](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/equal-width-text-lines) | O | Poster-style equal lines are not needed for a scientific workspace. |
| [export html media from canvas](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/export-html-media-from-canvas) | E | Canvas export recipe is unrelated and experimental. |
| [expose canvas content to browser features](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/expose-canvas-content-to-browser-features) | E | Origin Trial HTML-in-canvas is not adopted; stable labeled DOM tables supply alternatives. |
| [improve text layout and legibility](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/improve-text-layout-and-legibility) | A | Balance short headings and use readable paragraph wrapping. |
| [precise text alignment](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/precise-text-alignment) | O | Use ordinary alignment first; text-box trimming is an optional enhancement. |
| [shaped cutouts](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/shaped-cutouts) | O | No cutout effect is required. |
| [soft edge content fade](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/soft-edge-content-fade) | O | Optional scroll hint only; never obscure scientific data or focus. |
| [browser ui theming](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/browser-ui-theming) | A | Theme native controls without replacing native behavior. |
| [typography](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/typography) | A | Use relative type, flexible text boxes, readable line lengths and 200% text verification. |
| [visual effects](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/visual-effects) | O | Quiet surfaces need no new effects. |
| [visually stable font fallbacks](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/visually-stable-font-fallbacks) | A | Check font swapping and fallback metrics; avoid first-load shifts. |
| [visually stable mixed fonts](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/visually-stable-mixed-fonts) | A | Retain consistent numeral and fallback metrics across UI and scientific symbols. |
| [visually texture content](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/visually-texture-content) | O | Texture would add visual noise and is not required. |

### Ui Atoms
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [scroll progress indicator](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/scroll-progress-indicator) | O | No lengthy narrative flow currently needs a progress indicator. |
| [carousel slide effects](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/carousel-slide-effects) | N | No carousel. |
| [component specific light dark theme](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/component-specific-light-dark-theme) | O | A separate component theme is not needed. |
| [position aware tooltips](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/position-aware-tooltips) | O | Only needed if a new custom directional tooltip is introduced. |
| [pull to reveal](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/pull-to-reveal) | N | No pull-to-reveal interaction. |
| [responsive table](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/responsive-table) | A | Use semantic tables, contextual headers and keyboard-accessible internal scrolling. |
| [scroll position aware elements](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/scroll-position-aware-elements) | O | Back-to-top is optional; no floating affordance required. |
| [scrollability affordance hints](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/scrollability-affordance-hints) | A | Expose overflowing chart/table content with visible scrollbars or accurate edge hints. |
| [shrinking header on scroll](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/shrinking-header-on-scroll) | O | No shrinking header required when navigation is non-sticky/compact. |
| [single line overflow](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/single-line-overflow) | A | Allow wrapping where possible; preserve complete accessible names when truncation is unavoidable. |
| [state aware sticky headers](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/state-aware-sticky-headers) | O | Only relevant if sticky header state changes are added. |
| [icons](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/icons) | A | Use consistent vector icons; hide decorative icons and name icon-only controls. |
| [viewport aware dropdowns](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-atoms/viewport-aware-dropdowns) | A | Keep Share and other transient panels within the viewport; preserve trigger association. |

### Ui Components
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [accordion](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/accordion) | A | Use native details for optional explanations; verify keyboard and find-in-page. |
| [card](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/card) | A | Group one coherent result at a time; avoid nested decorative cards. |
| [carousel](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/carousel) | N | No carousel. |
| [menu](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/menu) | O | A disclosure of links is adequate; do not add menu roles without full keyboard support. |
| [scrollspy](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/scrollspy) | O | Methods anchor navigation does not require scrollspy. |
| [progress](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/progress) | O | Unknown-duration loads need status, not invented percentages. |
| [toolbar](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/toolbar) | O | Only use toolbar role with its single-tab-stop keyboard contract; labeled control groups may suffice. |
| [app menus](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/app-menus) | O | No application menu bar is needed. |
| [hovercard](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/hovercard) | O | No interactive hovercards required. |
| [breadcrumbs](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/breadcrumbs) | O | Current shallow navigation needs no breadcrumb hierarchy. |
| [copy button](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/copy-button) | A | Clipboard action must report success/failure and retain a selectable-link fallback. |
| [persistent app tours](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/persistent-app-tours) | O | User asked to reduce interruptions; do not add a tour. |
| [persistent toast notifications](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/persistent-toast-notifications) | O | Existing non-blocking status can remain inline; no toast stack required. |
| [dark mode toggle](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/dark-mode-toggle) | O | Theme switch is optional and outside current palette-preservation scope. |
| [dialog](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/dialog) | A | Use native dialog semantics, focus management and dismissal; avoid redundant ARIA/focus traps. |
| [spinner](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/spinner) | A | Expose loading state semantically and support reduced motion. |
| [navigation drawer](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/navigation-drawer) | O | Only if mobile navigation becomes an off-canvas drawer; inline disclosure remains valid. |
| [progress ring](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/progress-ring) | O | No measurable progress task needs a ring. |
| [navbar](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/navbar) | A | Keep current page identifiable and all navigation reachable on small screens. |
| [stack drill down](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/stack-drill-down) | O | URL view restoration is required; swipe-based stacked navigation is optional. |
| [checkbox](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/checkbox) | N | No checkbox redesign required. |
| [tabs](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/tabs) | A | Page navigation is not ARIA tabs; true tab widgets need complete keyboard semantics. |

### Ui Behaviors
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [scroll entry exit effects](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scroll-entry-exit-effects) | O | Scroll reveals are unnecessary and may hide important data. |
| [anchor positioning tab underline](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/anchor-positioning-tab-underline) | O | Static selection underline is sufficient. |
| [animate element entry exit](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/animate-element-entry-exit) | O | Instant show/hide is acceptable; optional animation must respect reduced motion. |
| [animate to from top layer](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/animate-to-from-top-layer) | O | Top-layer animation is optional; native behavior matters first. |
| [drag](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/drag) | O | No draggable floating windows needed. |
| [parallax scroll effects](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/parallax-scroll-effects) | O | Parallax adds noise and is not needed. |
| [carousel snap highlights](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/carousel-snap-highlights) | N | No carousel. |
| [consistent cross document transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/consistent-cross-document-transitions) | N | No cross-document transitions. |
| [dynamic sibling animations](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/dynamic-sibling-animations) | O | No staggered reveal needed. |
| [cross document transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/cross-document-transitions) | N | No cross-document transitions. |
| [custom button actions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/custom-button-actions) | O | Native buttons and React handlers are sufficient; invoker API is optional. |
| [declarative dialog popover control](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/declarative-dialog-popover-control) | O | Native showModal is valid; declarative invokers would require feature support. |
| [directional navigation transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/directional-navigation-transitions) | O | Directional animation is optional; keep context and history correct. |
| [dynamic sort](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/dynamic-sort) | O | No user-defined reordering flow present. |
| [highlight text ranges](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/highlight-text-ranges) | O | No text-search highlighting feature present. |
| [interactive content reveal](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/interactive-content-reveal) | O | Pointer-reveal decoration is inappropriate for essential results. |
| [interest triggered action previews](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/interest-triggered-action-previews) | O | No predictive preview needed; preserve stable actions. |
| [light dismiss a dialog](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/light-dismiss-a-dialog) | A | Native closedby plus guarded fallback; clicks inside padding must not dismiss. |
| [motion](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/motion) | A | Respect reduced motion; avoid layout-property animation and perpetual decorative animation. |
| [move dom element without losing state](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/move-dom-element-without-losing-state) | O | No live DOM reparenting required. |
| [persistent top layer ui](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/persistent-top-layer-ui) | O | No moving top-layer DOM nodes required. |
| [physics based easing](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/physics-based-easing) | O | No spring physics needed. |
| [platform controls dismiss dialog](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/platform-controls-dismiss-dialog) | A | Retain platform dismissal of native modal dialogs. |
| [prevent page scroll under modal dialog](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/prevent-page-scroll-under-modal-dialog) | A | Contain dialog/backdrop scrolling without locking the document root. |
| [drag and drop](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/drag-and-drop) | O | No list reordering present. |
| [same document transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/same-document-transitions) | O | Optional view transitions; must not delay input or navigation. |
| [scoped component transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scoped-component-transitions) | O | No component transition system required. |
| [scroll snap realtime feedback](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scroll-snap-realtime-feedback) | O | No snap-driven carousel state. |
| [scroll snap state sync](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scroll-snap-state-sync) | O | No snap-driven carousel state. |
| [scrollytelling](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scrollytelling) | O | No scroll-driven narrative required. |
| [search hidden content](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/search-hidden-content) | A | Keep static explanatory content in details or searchable panels, not inaccessible hiding. |
| [scroll target on load](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scroll-target-on-load) | O | Linked week/year restoration exists; native focus/scroll is enough without special scroll-start API. |
| [interest triggered tooltips](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/interest-triggered-tooltips) | A | Essential meaning stays visible/on-demand; never rely solely on mouse hover titles. |
| [group element transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/group-element-transitions) | O | No animated reordering required. |
| [sortable table](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/sortable-table) | O | Only applicable if table sorting is added; current fixed scientific order is deliberate. |
| [spatial navigation](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/spatial-navigation) | A | Arrow navigation must follow visual grid order and preserve normal input behavior. |
| [swipe to remove](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/swipe-to-remove) | O | No destructive swipe action required. |
| [swipe to reveal](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/swipe-to-reveal) | O | No swipe-only actions required. |
| [scroll completion effects](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/scroll-completion-effects) | A | Focus/scroll transitions must not leave focus off screen; honor reduced motion. |
| [2d panning](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/2d-panning) | E | Single-engine volatile panning API is not adopted; use stable native scrolling and pointer controls. |

### User Experience
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [form factor adaptation](https://developer.chrome.com/docs/modern-web-guidance/guides/user-experience/form-factor-adaptation) | A | 24px minimum target, 44px touch recommendation, 320px reflow and safe-area handling. |
| [natural interactions](https://developer.chrome.com/docs/modern-web-guidance/guides/user-experience/natural-interactions) | A | Distinct hover/press/focus states and native scrolling/disclosure behavior. |
| [content first noise reduction](https://developer.chrome.com/docs/modern-web-guidance/guides/user-experience/content-first-noise-reduction) | A | One primary content surface; compact navigation; remove repetitive instructions and headings. |

### Forms
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [animated select picker](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/animated-select-picker) | O | Native select needs no animated picker. |
| [brand consistent forms](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/brand-consistent-forms) | A | Keep native controls and use the brand accent through supported CSS. |
| [slider](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/slider) | A | Native range inputs need labels, limits, keyboard behavior and readable current values. |
| [branded select styling](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/branded-select-styling) | A | Native select remains baseline; enhanced picker styling must retain fallback. |
| [autofill payment form](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/autofill-payment-form) | N | No payments. |
| [autofill sign in form](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/autofill-sign-in-form) | N | No sign-in. |
| [autofill sign up form](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/autofill-sign-up-form) | N | No sign-up. |
| [switch](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/switch) | O | No switch-style setting currently needed. |
| [autofill address form](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/autofill-address-form) | N | No address collection. |
| [custom select picker layouts](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/custom-select-picker-layouts) | O | Native picker layout is adequate. |
| [autofill highlight inputs](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/autofill-highlight-inputs) | O | No stored personal profile form to autofill. |
| [form fields automatically fit contents](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/form-fields-automatically-fit-contents) | A | Control width must hold actual content without clipping country/date labels. |
| [forms](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/forms) | A | Semantic labeled forms, intentional submit behavior and associated errors. |
| [ime safe enter submit](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/ime-safe-enter-submit) | O | No chat or inline free-text Enter-submit behavior. |
| [required field feedback](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/required-field-feedback) | A | Do not mark untouched required fields invalid. |
| [rich media picker](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/rich-media-picker) | O | Country options need no rich media picker. |
| [select menu interaction](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/select-menu-interaction) | O | Country has valid default; no forced empty required choice is needed. |
| [sms otp form](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/sms-otp-form) | N | No OTP authentication. |
| [validate input after interaction](https://developer.chrome.com/docs/modern-web-guidance/guides/forms/validate-input-after-interaction) | A | Display editing errors after interaction or submission, rather than on initial load. |

### Html
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [accessible web components](https://developer.chrome.com/docs/modern-web-guidance/guides/html/accessible-web-components) | N | React app has no custom elements. |
| [custom elements](https://developer.chrome.com/docs/modern-web-guidance/guides/html/custom-elements) | N | No custom elements. |
| [form associated custom elements](https://developer.chrome.com/docs/modern-web-guidance/guides/html/form-associated-custom-elements) | N | No form-associated custom elements. |
| [html](https://developer.chrome.com/docs/modern-web-guidance/guides/html/html) | A | One h1/main, semantic landmarks, native controls and no disabled zoom. |
| [prerendering custom elements](https://developer.chrome.com/docs/modern-web-guidance/guides/html/prerendering-custom-elements) | N | No custom-element server rendering. |
| [shadow dom](https://developer.chrome.com/docs/modern-web-guidance/guides/html/shadow-dom) | N | No Shadow DOM component system. |
| [styling web components](https://developer.chrome.com/docs/modern-web-guidance/guides/html/styling-web-components) | N | No Shadow DOM component system. |
| [web components](https://developer.chrome.com/docs/modern-web-guidance/guides/html/web-components) | N | No Web Components migration. |

### Css
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [animate to intrinsic sizes](https://developer.chrome.com/docs/modern-web-guidance/guides/css/animate-to-intrinsic-sizes) | O | Disclosure size animation is optional. |
| [calculate with intrinsic sizes](https://developer.chrome.com/docs/modern-web-guidance/guides/css/calculate-with-intrinsic-sizes) | O | Ordinary intrinsic sizing works without calc-size. |
| [child state based styling](https://developer.chrome.com/docs/modern-web-guidance/guides/css/child-state-based-styling) | O | State selectors may simplify styles; not a requirement to add state. |
| [atrule support conditionals](https://developer.chrome.com/docs/modern-web-guidance/guides/css/atrule-support-conditionals) | O | Use feature queries when adding uncertain CSS support; no extra feature is required. |
| [content based styling](https://developer.chrome.com/docs/modern-web-guidance/guides/css/content-based-styling) | O | Only needed when child-content presence changes layout. |
| [css layout](https://developer.chrome.com/docs/modern-web-guidance/guides/css/css-layout) | A | Flexible grid/flex with container queries; do not hide layout overflow to mask defects. |
| [css](https://developer.chrome.com/docs/modern-web-guidance/guides/css/css) | A | Explicit cascade/tokens; avoid compounded override sheets and unnecessary global resets. |
| [design token reactivity](https://developer.chrome.com/docs/modern-web-guidance/guides/css/design-token-reactivity) | A | Shared spacing/type/control tokens prevent section-level visual drift. |
| [fluid scaling](https://developer.chrome.com/docs/modern-web-guidance/guides/css/fluid-scaling) | A | Relative bounds in fluid type; no viewport-only text sizing. |
| [individual transform properties](https://developer.chrome.com/docs/modern-web-guidance/guides/css/individual-transform-properties) | O | Individual transforms useful if motion added; no new animation required. |
| [overflow clipping control](https://developer.chrome.com/docs/modern-web-guidance/guides/css/overflow-clipping-control) | A | Do not clip focus outlines or content to conceal layout issues. |
| [reduce style repetition](https://developer.chrome.com/docs/modern-web-guidance/guides/css/reduce-style-repetition) | O | CSS functions unnecessary for this scale; tokens suffice. |
| [responsive design](https://developer.chrome.com/docs/modern-web-guidance/guides/css/responsive-design) | A | Responsive component layouts, dynamic viewport limits and space reserved for media. |
| [selector atrule combinations](https://developer.chrome.com/docs/modern-web-guidance/guides/css/selector-atrule-combinations) | O | Selector combinations are an optional maintainability technique. |
| [usage aware component variations](https://developer.chrome.com/docs/modern-web-guidance/guides/css/usage-aware-component-variations) | O | No context-sensitive component style-query system needed. |
| [size aware styling](https://developer.chrome.com/docs/modern-web-guidance/guides/css/size-aware-styling) | A | Use named container queries where components appear in different available widths. |
| [style parent with has](https://developer.chrome.com/docs/modern-web-guidance/guides/css/style-parent-with-has) | O | Optional invalid-field grouping; correct errors are the requirement. |
| [dynamic sibling styling](https://developer.chrome.com/docs/modern-web-guidance/guides/css/dynamic-sibling-styling) | O | No index/count-driven decorative styling needed. |

### Js
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [calculate event differentials](https://developer.chrome.com/docs/modern-web-guidance/guides/js/calculate-event-differentials) | O | No elapsed duration arithmetic to modernize. |
| [capture location agnostic data](https://developer.chrome.com/docs/modern-web-guidance/guides/js/capture-location-agnostic-data) | A | Keep date-only filters location-independent; preserve UTC/local scientific distinctions. |
| [coordinate global events](https://developer.chrome.com/docs/modern-web-guidance/guides/js/coordinate-global-events) | N | No event scheduling feature; scientific timestamp semantics stay unchanged. |
| [sort high precision timestamps](https://developer.chrome.com/docs/modern-web-guidance/guides/js/sort-high-precision-timestamps) | N | No nanosecond timestamp sorting need. |
| [support global calendar systems](https://developer.chrome.com/docs/modern-web-guidance/guides/js/support-global-calendar-systems) | N | Scientific Gregorian record; no alternate calendar product requirement. |

### Wasm
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [cpp on the web](https://developer.chrome.com/docs/modern-web-guidance/guides/wasm/cpp-on-the-web) | N | No C/C++ or WebAssembly component. |

### Performance
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [break up long tasks](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/break-up-long-tasks) | A | Measure long interactions before optimizing; chunk work only when measurements warrant it. |
| [calculate total foreground time](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/calculate-total-foreground-time) | N | No foreground-duration analytics. |
| [conditional async dependencies](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/conditional-async-dependencies) | O | Conditional polyfills only when a needed capability is absent. |
| [batch analytics events](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/batch-analytics-events) | N | No analytics event batching. |
| [defer rendering heavy content](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/defer-rendering-heavy-content) | A | Defer hidden heavy views; any content-visibility needs intrinsic size and focus testing. |
| [defer work until scroll ends](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/defer-work-until-scroll-ends) | O | No heavy scroll handler identified; do not add one. |
| [deliver optimized decorative images](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/deliver-optimized-decorative-images) | O | No raster hero decoration required. |
| [deprioritize background fetches](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/deprioritize-background-fetches) | A | Avoid background loading that competes with the selected view. |
| [detect initial visibility state](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/detect-initial-visibility-state) | O | Precise initial-visibility telemetry is not needed for current runtime visibility handling. |
| [efficient background processing](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/efficient-background-processing) | A | Pause offscreen/hidden-tab globe rendering and dispose resources when removed. |
| [faster spa view transitions](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/faster-spa-view-transitions) | A | Preserve useful view state without retaining unbounded WebGL resources. |
| [flicker free client side ab testing](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/flicker-free-client-side-ab-testing) | N | No A/B testing service. |
| [identify inp causes](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/identify-inp-causes) | A | Measure interaction latency; an observed fast interaction is not field INP certification. |
| [identify heavy scripts](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/identify-heavy-scripts) | A | Inspect long animation frames when available; do not add third-party analytics implicitly. |
| [improve next page load performance](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/improve-next-page-load-performance) | O | No speculative cross-document prefetch needed for the single-page app. |
| [lazy load video and audio](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/lazy-load-video-and-audio) | N | No video/audio assets. |
| [interaction paint timing](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/interaction-paint-timing) | A | Use feature-detected performance observations if measuring soft navigation. |
| [optimize image priority](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/optimize-image-priority) | O | No primary raster LCP image; do not add one for this recipe. |
| [optimize preload priority](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/optimize-preload-priority) | A | Only preload proven critical assets; font CORS and resource priorities must be correct. |
| [optimize script priority](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/optimize-script-priority) | A | Keep module loading deferred and heavy features lazy; no blanket high-priority scripts. |
| [interactions in complex layouts](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/interactions-in-complex-layouts) | A | Inspect chart/layout work for avoidable reflows; containment cannot clip content. |
| [out of order html streaming](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/out-of-order-html-streaming) | O | No streaming server in the static Pages app. |
| [performance](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/performance) | A | Measure load/runtime behavior, minimize unreachable CSS/JS and avoid font import chains. |
| [full session analytics](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/full-session-analytics) | N | No session analytics collection. |
| [resolution optimized pseudo elements](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/resolution-optimized-pseudo-elements) | O | No image pseudo-element assets currently need density variants. |
| [schedule tasks by priority](https://developer.chrome.com/docs/modern-web-guidance/guides/performance/schedule-tasks-by-priority) | O | Optional scheduler APIs only after profiling proves work needs prioritization. |

### Accessibility
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [accessibility](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/accessibility) | A | Keyboard, visible focus, heading structure, names, errors and actual accessibility testing. |
| [accessible error announcement](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/accessible-error-announcement) | A | Match aria-invalid and announced errors to user interaction state. |
| [accessible generated content](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/accessible-generated-content) | A | Keep labels/caveats in real DOM; pseudo-elements provide decoration only. |
| [respect os text scale](https://developer.chrome.com/docs/modern-web-guidance/guides/accessibility/respect-os-text-scale) | A | Opt into OS text scaling; leave root size browser-controlled; test scaling and reflow. |

### Security
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [validate origins](https://developer.chrome.com/docs/modern-web-guidance/guides/security/validate-origins) | O | No cross-document message or external origin validation flow in current app. |
| [client side encryption](https://developer.chrome.com/docs/modern-web-guidance/guides/security/client-side-encryption) | N | No client-side confidential records to encrypt. |
| [local network access](https://developer.chrome.com/docs/modern-web-guidance/guides/security/local-network-access) | N | Public static app should not access local network. |
| [passkey authentication](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkey-authentication) | N | No authentication. |
| [passkey conditional create](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkey-conditional-create) | N | No authentication. |
| [passkey management](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkey-management) | N | No authentication. |
| [passkey reauthentication](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkey-reauthentication) | N | No authentication. |
| [passkey registration](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkey-registration) | N | No authentication. |
| [passkeys](https://developer.chrome.com/docs/modern-web-guidance/guides/security/passkeys) | N | No authentication. |
| [trusted types](https://developer.chrome.com/docs/modern-web-guidance/guides/security/trusted-types) | O | No unsafe HTML sink found; enforcing Trusted Types needs dependency testing. |
| [quick sign ins](https://developer.chrome.com/docs/modern-web-guidance/guides/security/quick-sign-ins) | N | No authentication. |
| [restrict outbound connections](https://developer.chrome.com/docs/modern-web-guidance/guides/security/restrict-outbound-connections) | E | Connection-Allowlist needs explicit staged policy/reporting design; no experimental rollout in a visual preview. |
| [sanitize untrusted html](https://developer.chrome.com/docs/modern-web-guidance/guides/security/sanitize-untrusted-html) | O | No untrusted HTML insertion; keep React escaping instead of adding a sanitizer. |
| [secure external subresources](https://developer.chrome.com/docs/modern-web-guidance/guides/security/secure-external-subresources) | A | Audit third-party font resources, CORS and referrer leakage; dynamic CSS cannot use fixed SRI blindly. |
| [digital signatures](https://developer.chrome.com/docs/modern-web-guidance/guides/security/digital-signatures) | N | No client-side signature workflow. |
| [verify email ownership](https://developer.chrome.com/docs/modern-web-guidance/guides/security/verify-email-ownership) | N | No user email accounts. |
| [security](https://developer.chrome.com/docs/modern-web-guidance/guides/security/security) | A | HTTPS, safe DOM sinks and tested security headers; no unnecessary auth infrastructure. |

### Privacy
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [privacy](https://developer.chrome.com/docs/modern-web-guidance/guides/privacy/privacy) | A | No new tracking or permission collection; audit third-party requests and shared URL leakage. |

### Pwa
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [install web app](https://developer.chrome.com/docs/modern-web-guidance/guides/pwa/install-web-app) | O | Installability is a separate product feature, not needed for this UI redesign. |
| [migrate web app origin](https://developer.chrome.com/docs/modern-web-guidance/guides/pwa/migrate-web-app-origin) | N | No installed PWA migration. |

### Built In Ai
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [language detection](https://developer.chrome.com/docs/modern-web-guidance/guides/built-in-ai/language-detection) | N | No language-detection feature. |
| [language model](https://developer.chrome.com/docs/modern-web-guidance/guides/built-in-ai/language-model) | N | No in-browser language model. |
| [summarizer](https://developer.chrome.com/docs/modern-web-guidance/guides/built-in-ai/summarizer) | N | No automatic scientific summarization. |
| [translator](https://developer.chrome.com/docs/modern-web-guidance/guides/built-in-ai/translator) | N | No in-browser translation feature. |

### Webmcp
| Guide | Scope | Application / reason |
| --- | --- | --- |
| [agentic forms](https://developer.chrome.com/docs/modern-web-guidance/guides/webmcp/agentic-forms) | N | No requested agent-control forms. |
| [agentic javascript tools](https://developer.chrome.com/docs/modern-web-guidance/guides/webmcp/agentic-javascript-tools) | N | No requested agent-control tools. |
| [webmcp](https://developer.chrome.com/docs/modern-web-guidance/guides/webmcp/webmcp) | N | No WebMCP product requirement. |

## Final verification status

The final source review confirms a smaller presentation hierarchy: one page heading, a compact context row, navigation rail on desktop, mobile navigation disclosure, and monthly calendar on first arrival. Existing share URLs retain their former weekly default. Scientific interpretation text is either preserved beside results or moved into named native disclosures; no published data, Python computation or pipeline files changed relative to the first preview. The source diff check of `web/public/data`, `scripts`, `firetrace` and `tests` is empty.

Legacy shell styles now occupy an explicit lower-priority cascade layer, rather than competing as independent unlayered override sheets. Local CSS imports here are resolved by Vite during build; the performance concern is a runtime network import chain, not a source-level bundled import. New shell/Rhythm/Earth type uses relative units. The native dialog uses overscroll containment and no longer locks the HTML root. Weekly cells specify 24px base minimums and 44px coarse-pointer minimums with 1,488px/2,550px internally scrollable surfaces; monthly cells use 24px/44px minimums.

Browser evidence supplied by the integration lead: 320px monthly calendar reflow across all seven countries without page-level horizontal overflow; rendered weekly cells measured 24 by 24 pixels with 3px gaps; keyboard arrow movement, Enter opening evidence, Escape dismissal and focus return; Rhythm country-result focus; local Earth rendering. This audit agent independently inspected source, not those browser sessions.

The three final source findings were corrected before the preview build: selected months now use a border/outline with explicit forced-colors selection and focus rules; essential select/search controls use the control token (3.81:1 against the panel); active Share, area, month and reliability text uses relative units. Forced-colors behavior is source-reviewed, not a completed runtime emulation test.

Integration checks passed: 112 Python tests, 178 web tests, TypeScript and the root production build. The build has 9,021 files totaling 310,977,010 bytes; the largest is 12,999,487 bytes, below the 25 MiB Pages per-file limit. The existing lazy Globe bundle still triggers the advisory 500 kB chunk warning. At 320px the share panel remains within the viewport; copy feedback and the selectable URL both render. Local custom-area point/radius selection, US FRP disclosure, Methods hierarchy, and the final desktop Earth sidebar layout were exercised. Deployed-runtime checks are recorded separately in the preview receipt under the ignored `work/atlas-preview` directory.

Runtime CSP enforcement, font loading on the deployed preview, performance measurements, OS text scaling, full screen-reader coverage and physical phone interaction remain separate evidence requirements. Do not present this report as a 208-guide compliance certificate.

### Bounded foundation corrections implemented

- **Font privacy and loading:** `web/index.html` no longer requests Google Fonts CSS or font servers. `web/src/fonts.css` uses 14 original Google Fonts WOFF2 subsets: DM Sans 400–700 and IBM Plex Mono 400/500. Their total size is 164,684 bytes; only the 36,932-byte DM Sans Latin file is preloaded. Other subsets load when their glyphs are used. Both SIL Open Font License files and source/SHA-256 provenance accompany the files in `web/public/fonts`. Static verification confirmed each referenced local file, its WOFF2 signature and recorded hash. Actual browser font loading is part of the final preview check.
- **OS text sizing:** the document retains `<meta name="text-scale" content="scale">`. Root font size remains browser controlled. This is implementation evidence, not a physical-device text-scaling test.
- **JavaScript fallback:** a native noscript message explains the interactive requirement and links directly to the published data index and NASA FIRMS.
- **Preview security foundations:** `web/public/_headers` supplies `nosniff`, `no-referrer`, denial of unused camera/microphone/geolocation permissions, and an origin-limited CSP. Scripts, fonts and fetches are same-origin. Inline styles remain allowed because React supplies dynamic scientific chart styles; inline scripts and eval are not permitted. Images permit same-origin/data/blob for existing rendering/export patterns. Objects, base URL injection and embedding are blocked. No new tracking endpoint, experimental network allowlist, HSTS rollout or global noindex rule was added.
- **CSP validation boundary:** static source review found same-origin application data/world geometry fetches and no remote scripts. The new policy must still be checked against the deployed preview's actual response headers, font loading, lazy modules, both Earth layers, exports and browser console. Vite's development server does not enforce the Pages `_headers` file.

All changes are isolated to the experimental branch. Production headers and files have not been changed by this audit agent.

## Attribution

Guide references: Google Chrome for Developers, [Modern Web Guidance](https://developer.chrome.com/docs/modern-web-guidance/guides), catalogue updated 2026-11-10, reviewed 2026-11-15. The source site licenses its documentation under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and code samples under Apache 2.0. This report contains original applicability decisions and links, not copied guide bodies.
