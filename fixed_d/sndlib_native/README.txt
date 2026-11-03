SNDLIB TOPOLOGY-ONLY FALLBACK FILES

These files are provided because the official SNDlib .action download routes
were returning HTTP 404 on 30 October 2026.

The node coordinates and undirected physical links were extracted from the
public FOCS-AI/optrix research-data mirror of SNDlib topologies:
https://github.com/FOCS-AI/optrix

Expected topology sizes:
  abilene:  12 nodes, 15 links
  polska:   12 nodes, 18 links
  nobel-us: 14 nodes, 21 links

They intentionally omit demands, original link capacities, and costs. The
fixed-d package uses only node IDs and physical links; it independently assigns
controlled multistate capacities according to the recorded seeds. Consequently,
the omitted fields have no role in the experiment.

Copy the three .txt files into the sndlib_native subfolder of the extracted
fixed_d_dmp_experiment_v1.2 package. Retain this README with the experiment's
archived input data so the provenance is transparent.
