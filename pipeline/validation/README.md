# Separate scientific checks

`science_checks` reads the verified exact-count preparations and reductions made
by `pipeline.streaming`. It does not update production models, test metrics,
public JSON, or the supported observation years.

The completed seven-country check can be reproduced in this workspace with:

```powershell
.venv/Scripts/python.exe -m pipeline.validation.science_checks --preparations work/phase3/nepal-us work/phase3/bangladesh-egypt work/phase3/australia-india-brazil --analyses work/phase3/nepal-us-analysis work/phase3/bangladesh-egypt-analysis work/phase3/australia-india-brazil-analysis --model work/phase3/seven-country-evaluation/harmonization_model.json --output work/scientific-validation-repeat
```

For a clean checkout, first run the documented streaming preparation/reduction
workflow, then pass those output directories and its locked model. The sources
must have matching manifest fingerprints and complete adjacent annual archives.
An existing output directory is refused so prior protocols and results survive.

The protocol is written before measurements. Grid selection uses 2013–2017;
grid diagnostics use 2018–2019 with fixed released weights. That block also
selected the released country models, so this is sensitivity analysis, not an
independent test. Bridge fitting uses 2003–2007, with a separate 2008–2011
validation block and whole-training-year bootstrap. Neither calculation uses
2020–2024, and neither publishes a 2001–2002 reconstruction.

Run `python -m pytest tests/test_science_checks.py -q` for boundary, multiplicity,
training-isolation and aggregation-interpretation checks. The completed report
and numerical tables are under `reports/scientific_validation/`.
