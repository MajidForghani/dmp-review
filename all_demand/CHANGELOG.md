# Changelog

## 1.1.0 FINAL

- Added the Yeh (2018) all-demand algorithm as a primary exact comparator.
- Added exact reproduction of Yeh's published Fig. 1 / Tables II--VI sets.
- Added incremental Lambda updates from Lemma 10.
- Added exact tuple confirmation for the logarithmic-prime merge mechanism.
- Added a 37-network digest regression audit against validated Bai-2021 output.
- Expanded primary rankings to Yeh-2018, Bai-2021, and repeated F-B-2017.
- Kept literal Yeh--Zuo-2019 as a correctness diagnostic only.
- Separated primary exact disagreements from expected diagnostic disagreements
  in `output_audit.json`.
- Restricted fastest-method labels and output-consistency checks to complete
  primary algorithms.

## 1.0.0

- Initial all-demand package with repeated F-B-2017, literal Yeh--Zuo-2019,
  and Bai-2021.
