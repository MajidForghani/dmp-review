# Release provenance

This public-release tree combines the final experiment packages and the exact
result archives supplied after execution. The source archive SHA-256 values are:

| Source archive | SHA-256 |
|---|---|
| `fixed_d_dmp_experiment_v1.2.1_FINAL.zip` | `018000e1a0f32ac305d42faa098d7107770c5fc1209151cbf4aa8a43aebf74e4` |
| `results_fixed-d_final_v1.2.1.zip` | `6df89cf40b0c28688c764e6523465b32333da47b7a7ad116e4fb2478f5810545` |
| `fixed_d_complete_v1.2.1.zip` | `ffd97a82a38744d5ee6d808595355d580e6ee58a45e561c07d24570e38459519` |
| `all_demand_dmp_experiment_v1.1_FINAL.zip` | `d6fb1c9ecf99c2a5fb500f21853f5ecb063dfe234f987a79b1aa79c1cf35fa90` |
| `all_demand_final_v1.1.zip` | `6d9bb621e03ef8137b9887d54210f969f926c6827aa1bcd9f73580d1da768b17` |
| `all_demand_final_v1.1(1).zip` | `b87b04ccada65e5561a5335c1cad79a444d9ee38c90c0d30a3396502928f7ee5` |

## Public-release normalization

Only the following nonnumerical changes were made while assembling the public
repository:

1. Python cache files were removed.
2. Machine-specific absolute paths in manifests, configuration files, audits,
   and CSV `instance_path` fields were changed to repository-relative paths.
3. The fixed-demand deterministic corpus was regenerated from its archived
   scripts, seeds, and topology inputs so that all 94 instance JSON files are
   present in the repository.
4. Manifest hashes in the public `run_config.json` files were refreshed after
   path normalization. The hashes recorded during the original runs are
   retained as `original_run_manifest_sha256`.
5. Summary files were regenerated from the unchanged numerical observations.

No timing, phase, memory, counter, status, output-cardinality, or output-digest
value was changed. The environment files preserve the hardware and software
information recorded during the original executions.

