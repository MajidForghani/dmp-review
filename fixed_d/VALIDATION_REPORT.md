# Validation report

## Evidence included in the package

The implementations are tested by exact set equality, not only by output count.
`python validate.py` performs two complementary checks:

1. Five deterministic fixtures, including transcribed examples associated with
   Lin et al. (1995), Huang et al. (2020), Niu et al. (2020), and Wu (2025), plus
   a cyclic stress fixture.
2. Twenty small independently generated directed networks (ten acyclic and ten
   potentially cyclic), each at two demand fractions when distinct.

For every case, every algorithm's output set is compared with an exhaustive
oracle that enumerates the complete Cartesian product of arc states and applies
the mathematical d-MP definition. The validation fails on any missing or extra
vector.

Wu's printed example uses the method's internal edge order; the fixture converts
those vectors back to the canonical network edge order before comparison. Huang's
residual binding-group rule is implemented separately because the paper does not
extend its beta set in that branch; global minimal comparison is consequently
required.

## Re-run record

On the packaged code, all five methods matched the oracle on all five fixtures
and all twenty randomized networks. Run `python validate.py` on the experimental
machine and retain its console output with the study archive.

## Limits of this evidence

- Agreement with an oracle on finite instances is strong implementation evidence,
  not a proof that the code is error-free for every input.
- The package assumes consecutive integer component states. It is not valid to
  apply the one-unit decrement test unchanged to nonconsecutive state spaces.
- Very large simple-path sets can make path-based methods impractical. The
  `--max-paths` guard turns such cases into recorded errors rather than silently
  truncating output.
- Python allocation peaks exclude native/runtime memory not tracked by
  `tracemalloc`; report the metric precisely as peak traced Python allocation.
- Experimental rankings apply to these reimplementations, machine, instances,
  and parameter choices.
