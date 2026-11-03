# Validation report

Validation date: 30 October 2026

Command: `python validate.py`

## Passed checks

- Bai et al. (2021) reproduces the published all-level counts 8/16/8/1.
- Yeh (2018) reproduces the published all-level counts 4/5/3/1 and includes
  the fifth 2-MP `(1,2,0,1,1,0)`.
- The literal Yeh--Zuo (2019) reconstruction reproduces the published counts
  4/4/3/1.
- Yeh-2018, Bai-2021, and repeated F-B-2017 agree exactly with an independent exhaustive
  arc-state oracle on the Yeh--Zuo network, four other published networks, and
  20 seeded small random networks.
- Exact output digests agree among the three primary methods in every check.
- Yeh-2018 also agrees with the previously validated Bai-2021 digest on all 37
  networks of the final corpus.
- The isolated worker, checkpointed runner, separate memory pass, audit files,
  summary CSV/TeX generation, and plotting pipeline passed an end-to-end smoke
  test.

## Expected diagnostic finding

Literal Yeh--Zuo-2019 omits `(1,2,0,1,1,0)` on its own Fig. 1 network. It was
also incomplete on three of the 20 small random oracle networks. This is an
algorithmic containment failure, not an implementation exception. Details and
the reporting decision are in `CORRECTNESS_AUDIT.md`.
