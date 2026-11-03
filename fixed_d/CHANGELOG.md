# Changelog

## 1.2.1

- Corrected the summary audit so fully timed-out cases are reported as
  unsolved rather than as output inconsistencies.
- Documented the calibrated SNDlib-derived final design: bidirected topology,
  capacity states 0--2, and held-out main seeds 40--41.
- No enumeration algorithm was changed.

## 1.2.0

- Separated three-repeat timing from a single independent peak-memory pass.
- Added fixed run-configuration hashing and safe checkpoint/resume checks.
- Added held-out final random-corpus generation and deterministic SNDlib suites.
- Added published-example cases and manifest merging.
- Added MP-generation time, path-overlap, rejection, flow-call, partition, and
  compressed-storage counters required by the revised manuscript.
- Added automatic case/algorithm summaries, phase tables, TeX tables,
  performance profiles, solved-instance curves, plots, and consistency audits.
- Retained timeouts as censored observations rather than substituting the time
  limit into completed-run averages.

## 1.1.0

- Corrected Niu phase accounting by removing nested verification time from
  `T_search`; this prevents double counting in `T_total`.
- Added the capacity range to generated random-instance names.
- Enumeration logic and expected d-MP sets are unchanged.

## 1.0.0

- Initial fixed-demand comparison package.
