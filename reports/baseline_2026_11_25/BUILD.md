# Consolidated baseline report

Follow-up analysis dated 25 November 2026, prepared for the intermediate deliverable. Two IEEE conference-format pages, including seven references. This is the consolidated intermediate report; LMS submission has not been performed.

From the repository root:

```bash
python scripts/audit_baseline.py
python scripts/build_baseline_report.py
mkdir -p output/pdf
cd reports/baseline_2026_11_25
tectonic --outdir ../../output/pdf main.tex
```

Tectonic 0.17.0 was used. The generated table reads provenance-checked files; all seven completed runs must be available. The 31B zero-shot capacity failure is described separately and never scored as 0% accuracy.

The reviewed final copy is `baseline_report.pdf`. Both rendered pages were inspected. T1 fonts and the original unmodified IEEEtran conference class are included. The original 31B report under `reports/intermediate/` is unchanged. The copied earlier small-model report folders are historical snapshots, superseded by this report for current review.
