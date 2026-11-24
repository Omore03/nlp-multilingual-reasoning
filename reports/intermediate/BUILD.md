# Build the intermediate report

The paper uses the actual IEEEtran 1.8b conference class from the [CTAN IEEEtran distribution](https://ctan.org/pkg/ieeetran). Its original README and license notice are preserved beside the class. Do not change the IEEE font sizes or margins to fit more content.

1. From the repository root, evaluate the real journal with the README command.
2. Run `python scripts/build_report_inputs.py` to generate the table from checked real outputs.
3. In `reports/intermediate/`, run `tectonic --outdir ../../output/pdf main.tex`.
4. Render every page and inspect the final PDF; the total must be at most three pages including references.

Tectonic 0.17.0 was used for this build, obtained from its [official release](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0). A normal LaTeX installation supporting IEEEtran can also compile the source. T1 font encoding is explicit so Tectonic uses the Times-compatible body fonts instead of silently falling back to Latin Modern. The compiler may download TeX support files; no model weights or paid service are needed.

`generated_results.tex` is an output, not a place to type scores by hand. Keep it synchronized with the real raw journal, manifest and evaluated artifacts. Report the actual collection date and disclose incomplete coverage. This paper does not claim the team met the earlier 23 November deadline.
