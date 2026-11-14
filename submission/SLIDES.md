# FIRETRACE: seven-slide presentation outline

Draft for adaptation to the verified event submission format. Do not assume a seven-slide allowance without checking the live submission instructions. Every bracketed result must be replaced from the generated report or removed.

## 1. The question

**Title:** Did fire activity change—or did our camera change?

Show one actual region's raw series with instrument provenance. Explain that a hotspot is a detection, not a separate fire. Do not label a real rise “fake” before evaluation.

**Speaker line:** “An apparent increase can mix environmental change with a change in what the instrument can detect.”

## 2. The person making the decision

**Title:** A fire manager needs a comparable history

Show the region selector and the historical calendar. State one task: identify periods of unusually high recorded activity relative to that region's historical season. Make clear this is historical context, not an emergency forecast.

**Evidence:** Nepal and the United States, 2013–2024. Show Nepal first; both have national totals and selected map cells.

## 3. The method

**Title:** A named reference, separate streams, an untouched test

Display a simple diagram: FIRMS → civil dates and stream separation → calibration → held-out evaluation → evidence card.

List B0 uncalibrated, B1 global ratio and M1 region/daynight/reported-FRP stratified ratio. Training 2013–2017; validation 2018–2019; test 2020–2024. Validation selects M1 for Nepal and B1 for the US. Do not imply the more complex method always wins.

## 4. The working demonstration

**Title:** Follow one conclusion back to its evidence

Demonstrate the raw/calibrated toggle, select one week, then open the evidence card. Show contributing observations, named scale, calibration interval and coverage caveat. A trend that persists is a legitimate result.

**On screen:** Real Nepal data, 2013–2024, M1 calibration. Select a week in the actual app and read its evidence card rather than inventing a local anecdote. The demo need not erase a trend. Any synthetic mechanism figure must carry “SYNTHETIC DATA” visibly.

## 5. What the tests say

**Title:** Compare the method with something simpler

Use the actual report table: model, region, period, aggregation, MAE and bias. Include baseline performance and a relevant failure/sensitivity case. Separate synthetic software verification from real-data evaluation.

**Result:** Nepal 2020–2024 monthly MAE: M1 30.20, B1 198.43, B0 2,474.43; selected M1 bias −8.08%. US monthly MAE: selected B1 1,606.30, M1 2,078.63, B0 31,835.40. Units are detections on the Aqua reference scale. Each monthly test comparison contains 60 periods. Include the US result to show that the simpler baseline can win.

## 6. The optional human-rhythm question

**Title:** Can we detect a reproducible weekly association?

Display the exact gate decision and why. If it passes, show separate streams and uncertainty with cautious interpretation. If it fails or is insufficient, show that result plainly and explain why the feature is disabled.

**Result:** Overall `insufficient_data`; US criterion passed in 3/3 streams with unflagged matching controls; Nepal criterion passed in 0/3 streams and matching-control qualification was insufficient. The other five configured countries were not evaluated. The production rhythm feature remains disabled. Never turn insufficient data into evidence of no effect.

## 7. What we built, and what comes next

**Title:** A reproducible comparison that shows its limits

Show the NASA source and the owner-private preview: https://firetrace-bhaktapur-2026.welcomingtulip8.chatgpt.site (deployment confirmation pending; not judge-accessible). A public source URL and judge-accessible hosting remain required before submission. State the two-country supported scope and measured outcome. Broader coverage, land-cover stratification and early-record calibration remain future work. Include the AI disclosure and “NASA does not endorse this project.”

**Closing line:** “FIRETRACE makes a fire trend's evidence inspectable before that trend becomes a decision.”
