# Recorded Lab 01 result — 2026-11-11

Cluster: `itz-s6fyum` — OpenShift 4.21.24.

Final v1.4.2 result, as pasted by the user:

- 22 Ansible tasks passed for repairing the unused `fusionfs1` StorageClass.
- `fusionfs1` live remote cluster ID: `12420798289407968864` (unique to this reservation).
- Correct `volBackendFs`: `lab01-external-scale-fs1`.
- Scale CSI created PVC and ran writer pod: `WRITE_OK: 16 MiB written and checksum recorded`.
- Writer pod deleted; fresh reader pod verified `/data/fusion-test.bin: OK` and `READ_OK: 16 MiB persisted and SHA-256 verified after pod recreation`.
- Test namespace removed. Final line: `LAB 01 SCALE EXTERNAL STORAGE: PASS`.
- Earlier user-provided log confirmed Fusion/Data Foundation/Ceph and Ceph persistence test passed; the Scale Operator, client nodes, remote connection and mount were healthy.

This is a historical validation record. It is **not** an instruction to reuse the old API, worker names, or remote cluster ID on a new lab.
