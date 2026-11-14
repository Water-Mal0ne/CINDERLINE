# FIRETRACE

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots  
**Team location:** Bhaktapur, Nepal  
**Submission status:** Results populated from generated reports. Public judge-accessible hosting and a public repository are still required before submission.

## Did fire activity change—or did our camera change?

Satellite fire records span instruments with different detection capabilities. Joining their counts can confuse a change in the observing system with a change on the ground. FIRETRACE makes that comparison inspectable for fire and land managers.

We use NASA FIRMS records and keep Terra, Aqua and VIIRS observations separate. We compare an uncalibrated baseline, a simple VIIRS-to-Aqua ratio and a stratified calibration. Model selection uses validation years; final evaluation uses withheld years. Results are expressed as Aqua-equivalent detections, never the “true number of fires.”

The application connects a burning-activity calendar to typical seasonal patterns, historical anomalies and evidence cards. Users can compare raw and calibrated series, inspect the contributing instruments and uncertainty, and export the displayed data. Missing observation coverage is distinguished from a zero count.

**Verified scope:** Nepal and the United States, 2013–2024.  
**Selected models:** M1 stratified calibration for Nepal; B1 global ratio for the US, selected using 2018–2019 validation daily MAE.  
**Held-out result:** On Nepal's 60 test months in 2020–2024, M1 monthly MAE was 30.20 Aqua-equivalent detections versus 198.43 for B1; M1 bias was −8.08%. In the US, the selected simpler B1 model had monthly MAE 1,606.30, versus 2,078.63 for M1. These are comparisons with Aqua observations, not ground-truth fire counts.  
**Owner-private preview:** [FIRETRACE preview](https://firetrace-bhaktapur-2026.welcomingtulip8.chatgpt.site), deployment confirmation pending. This URL is not judge-accessible.  
**Source and reproducibility:** Public repository URL required before submission; the local source and reports are included in the deliverable.

Our optional research module tests predefined rest-day patterns separately by instrument. It reports year-bootstrap intervals, corrected significance tests and diagnostic controls. **Current release decision: insufficient_data.** The US criterion passed in three streams; Nepal's predefined criterion passed in none. Other countries were not evaluated, so the US-plus-two-other-countries gate cannot pass. The feature stays disabled and the findings remain in the report. A weekly association cannot establish ignition cause.

Our contribution is a traceable path from an apparent change to its supporting evidence: instrument provenance, a reproducible comparison, validation against baselines and visible limits. We do not require harmonization to erase a trend.

**NASA resource:** [FIRMS country archives](https://firms.modaps.eosdis.nasa.gov/country/).  
**Scientific context:** [Earl, Simmonds and Tapper (2015)](https://doi.org/10.1002/2015GL066383).  
**AI disclosure:** Codex assisted with implementation, tests and documentation. See `AI_DISCLOSURE.md` for the exact scope. Synthetic examples are explicitly labeled and are not presented as real findings.

NASA does not endorse this project.
