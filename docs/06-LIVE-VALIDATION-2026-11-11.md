# Live deployment validation — November 11, 2026

**Release tested:** v2.2.0  
**Environment:** new disposable nine-node IBM TechZone cluster; OpenShift Container Platform 4.21.24  
**Method:** one `bash install-lab01.sh deploy` invocation, with explicit disk-claim and worker-reboot authorization  
**Result:** **PASS — all seven stages, no manual fixes during deployment**

## Results observed in the deployment log

| Stage | Result | Evidence |
|---|---|---|
| OpenShift preflight | PASS | All ClusterOperators Available, not Progressing/Degraded; MachineConfigPools updated |
| `fusion-ceph` | PASS | Fusion operator 2.14.1; Data Foundation service; three Ceph OSDs; StorageCluster Ready |
| `ceph-io-test` | PASS | 16 MiB persisted; remount and SHA-256 checksum verified; test namespace removed |
| `scale-nodeprep` | PASS | Dedicated Scale MachineConfigPool, 3/3 updated workers, isolated from Ceph infrastructure workers |
| `scale-operator` | PASS | A readiness assertion returned not-ready initially; wrapper retried automatically and succeeded |
| `scale-client` | PASS | Three-node data-access Scale client configured |
| `scale-external` | PASS | Existing remote server connected; `fs1` mounted; `fusionfs1` created using live cluster ID and local filesystem backend; 16 MiB remount/checksum test passed; namespace removed |
| `final-verification` | PASS | Fusion and Ceph readiness reconfirmed |

The final log ended with `PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.` The external IBM Storage Scale server was **not** installed or rebuilt by this workflow.

## Timing

- The v2.2 log filename indicates **20:31:58 UTC** (12:31:58 PM PST) at startup.
- The external Scale I/O test completed at **21:11:33 UTC** (1:11:33 PM PST).
- Final verification ran after that. **Approximate elapsed deployment time: 40 minutes**; the original log did not record the exact process exit timestamp.
- The pre-deployment `plan`, manual exploration, TechZone reservation creation, credential entry and file transfer are **not included** in this benchmark.

## Post-run improvements

The source used in this exact test was **v2.2.0**. The follow-on v2.3.0 candidate changes **only the runner's timing/logging and the Scale operator readiness + node pool diagnostic behavior**; it is **not yet live-validated**.

No access tokens, passwords, private kubeconfigs, or raw installation logs are included in this report. Full diagnostics must remain private.
