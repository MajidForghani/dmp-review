# Suggested GitHub upload procedure

Recommended repository name: `dmp-enumeration-benchmarks`.

## GitHub Desktop

1. Extract the release archive.
2. In GitHub Desktop, choose **File > Add local repository** and select the
   extracted `dmp-enumeration-benchmarks` folder.
3. If prompted, choose **Create a repository here**.
4. Enter an initial commit message such as `Public reproducibility release`.
5. Choose **Publish repository**, select the desired account, and make the
   repository public when ready.
6. Create a release tagged `v1.0.0` and attach the same ZIP archive if desired.
7. Copy the repository or release URL into the manuscript's code-and-data
   availability statement.

Before publishing, the authors may add their preferred license. No license was
selected automatically because licensing code and archived research data is an
author decision.

## Final local check

From the repository root, run:

```bash
python verify_release.py
python fixed_d/validate.py
python all_demand/validate.py
```

These commands are quick integrity and correctness checks; they do not repeat
the long timing experiments.

